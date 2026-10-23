import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db_session
from backend.app.db.models import AnalysisModel, BRDVersionModel, EvidenceModel
from backend.app.schemas.api import (
    AnalysisStartResponse,
    AnalysisStatusResponse,
    HumanReviewDecisionRequest,
    ImpactGraphResponse,
    RequirementUpdateRequest,
)
from backend.app.schemas.brd import BRDDocument, ReviewStatus
from backend.app.schemas.evidence import DiscoveredSymbol, EvidenceRecord, ScanSummary
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.impact_service import ImpactAnalysisService

router = APIRouter(prefix="/analyses", tags=["Analyses"])

@router.post("/repositories/{repository_id}/analyze", response_model=AnalysisStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    repository_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    try:
        analysis = await AnalysisService.start_analysis(repository_id, session)
        return AnalysisStartResponse(
            analysis_id=analysis.id,
            repository_id=repository_id,
            status=analysis.status,
            message="Analysis workflow dispatched successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    analysis = await session.get(AnalysisModel, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis not found: {analysis_id}")

    scan_summary_obj = ScanSummary(**analysis.scan_summary) if analysis.scan_summary else None

    return AnalysisStatusResponse(
        analysis_id=analysis.id,
        repository_id=analysis.repository_id,
        status=analysis.status,
        current_node=analysis.current_node,
        progress_percentage=analysis.progress_percentage,
        error=analysis.error_message,
        started_at=analysis.started_at.isoformat(),
        completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None,
        scan_summary=scan_summary_obj,
        validation_score=analysis.validation_score,
        review_status=ReviewStatus(analysis.review_status) if analysis.review_status in ReviewStatus.__members__.values() else ReviewStatus.PENDING,
    )

@router.get("/{analysis_id}/events")
@router.get("/{analysis_id}/stream")
async def stream_analysis_events(
    analysis_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    analysis = await session.get(AnalysisModel, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis not found: {analysis_id}")

    async def event_generator():
        q = AnalysisService.subscribe(analysis_id)
        try:
            # 1. Yield all historical events so the client catches up on everything
            history = AnalysisService.get_event_history(analysis_id)
            for ev in history:
                yield f"data: {json.dumps(ev)}\n\n"

            # If analysis is already in terminal state and history sent, close cleanly
            if analysis.status in ["completed", "awaiting_review", "failed"]:
                return

            # 2. Stream live events as each node executes
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") in ["completed", "failed"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment for SSE
                    yield ": ping\n\n"
        finally:
            AnalysisService.unsubscribe(analysis_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.get("/{analysis_id}/evidence", response_model=List[EvidenceRecord])
async def get_evidence(
    analysis_id: str,
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session)
):
    query = select(EvidenceModel).where(EvidenceModel.analysis_id == analysis_id)
    if category:
        query = query.where(EvidenceModel.category == category)
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    models = result.scalars().all()

    return [
        EvidenceRecord(
            id=m.id,
            repository_id=m.repository_id,
            relative_path=m.relative_path,
            symbol_name=m.symbol_name,
            start_line=m.start_line,
            end_line=m.end_line,
            source_excerpt=m.source_excerpt,
            category=m.category,
            extraction_method=m.extraction_method,
            validation_status=m.validation_status,
            metadata=m.metadata_json or {}
        )
        for m in models
    ]

@router.get("/{analysis_id}/symbols", response_model=List[DiscoveredSymbol])
async def get_symbols(analysis_id: str):
    cached = AnalysisService.get_cached_analysis_data(analysis_id)
    if not cached:
        return []
    return cached.get("symbols", [])

@router.get("/{analysis_id}/brd", response_model=BRDDocument)
async def get_brd(
    analysis_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    cached = AnalysisService.get_cached_analysis_data(analysis_id)
    if cached and cached.get("brd"):
        return cached["brd"]

    result = await session.execute(
        select(BRDVersionModel)
        .where(BRDVersionModel.analysis_id == analysis_id)
        .order_by(BRDVersionModel.version.desc())
    )
    latest = result.scalars().first()
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BRD not yet generated or analysis still pending.")

    return BRDDocument(**latest.brd_document)

@router.patch("/{analysis_id}/requirements/{requirement_id}", response_model=BRDDocument)
async def update_requirement(
    analysis_id: str,
    requirement_id: str,
    update: RequirementUpdateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    status_val = update.review_status or ReviewStatus.PENDING
    updated_brd = await AnalysisService.update_requirement_review(
        analysis_id=analysis_id,
        requirement_id=requirement_id,
        status=status_val,
        reviewer_name="Analyst",
        notes=update.reviewer_notes,
        session=session
    )
    if not updated_brd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement or analysis not found.")

    return updated_brd

@router.post("/{analysis_id}/review", response_model=BRDDocument)
async def submit_human_review(
    analysis_id: str,
    review: HumanReviewDecisionRequest,
    session: AsyncSession = Depends(get_db_session)
):
    analysis = await session.get(AnalysisModel, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    analysis.review_status = review.decision.value
    await session.commit()

    cached = AnalysisService.get_cached_analysis_data(analysis_id)
    if cached and cached.get("brd"):
        cached["brd"].review_status = review.decision
        return cached["brd"]

    result = await session.execute(
        select(BRDVersionModel)
        .where(BRDVersionModel.analysis_id == analysis_id)
        .order_by(BRDVersionModel.version.desc())
    )
    latest = result.scalars().first()
    if not latest:
        raise HTTPException(status_code=404, detail="BRD not found")
    brd = BRDDocument(**latest.brd_document)
    brd.review_status = review.decision
    return brd

@router.get("/{analysis_id}/impact-graph", response_model=ImpactGraphResponse)
async def get_impact_graph(analysis_id: str):
    cached = AnalysisService.get_cached_analysis_data(analysis_id)
    if not cached or not cached.get("brd"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis data or graph not found.")

    return ImpactAnalysisService.build_impact_graph(
        analysis_id=analysis_id,
        brd=cached["brd"],
        evidence=cached.get("evidence", []),
        symbols=cached.get("symbols", []),
        dependencies=cached.get("dependencies", [])
    )

