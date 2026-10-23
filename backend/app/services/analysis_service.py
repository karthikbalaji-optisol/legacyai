import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.langgraph_workflow import build_analysis_workflow
from backend.app.core.logging import logger
from backend.app.core.telemetry import (
    ANALYSIS_DURATION_SECONDS,
    ANALYSIS_TOTAL,
    EVIDENCE_EXTRACTED_TOTAL,
    EVIDENCE_VALIDATION_SCORE,
)
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import (
    AnalysisModel,
    BRDVersionModel,
    EvidenceModel,
    RepositoryModel,
    ReviewDecisionModel,
)
from backend.app.schemas.brd import BRDDocument, ReviewStatus

# Active in-memory cache for fast graph queries
_ANALYSIS_CACHE: dict[str, dict[str, Any]] = {}

# In-memory pub/sub and event history buffer for SSE streaming
_ANALYSIS_EVENTS: dict[str, list[dict[str, Any]]] = {}
_SUBSCRIBERS: dict[str, list[asyncio.Queue]] = {}

NODE_META: dict[str, dict[str, Any]] = {
    "validate_repository": {
        "step": 1,
        "progress": 10,
        "badge": "SECURITY",
        "summary": "Validating repository structure, sandbox directory, and security constraints."
    },
    "scan_source_code": {
        "step": 2,
        "progress": 25,
        "badge": "SCANNER",
        "summary": "Deterministic C# syntax & AST scanning across controllers, services, models, and routes."
    },
    "build_evidence_index": {
        "step": 3,
        "progress": 35,
        "badge": "EVIDENCE",
        "summary": "Constructing deterministic code evidence index with SHA-256 anchored line excerpts."
    },
    "extract_business_capabilities": {
        "step": 4,
        "progress": 45,
        "badge": "DOMAIN",
        "summary": "Mapping high-level enterprise capabilities, bounded contexts, and workflow responsibilities."
    },
    "extract_business_rules": {
        "step": 5,
        "progress": 55,
        "badge": "RULES",
        "summary": "Extracting decision logic, numerical thresholds, safety caps, and role requirements."
    },
    "generate_functional_requirements": {
        "step": 6,
        "progress": 65,
        "badge": "SPEC",
        "summary": "Synthesizing candidate functional requirements with Given/When/Then acceptance criteria."
    },
    "validate_evidence": {
        "step": 7,
        "progress": 75,
        "badge": "VALIDATOR",
        "summary": "Deterministic line-by-line verification against repository files on physical disk."
    },
    "identify_gaps_and_questions": {
        "step": 8,
        "progress": 85,
        "badge": "ANALYSIS",
        "summary": "Detecting missing architectural specifications and formulating stakeholder open questions."
    },
    "generate_brd": {
        "step": 9,
        "progress": 95,
        "badge": "BEDROCK",
        "summary": "Amazon Bedrock (Claude 3) structured BRD synthesis with zero-hallucination citation validation."
    },
    "await_human_review": {
        "step": 10,
        "progress": 100,
        "badge": "GOVERNANCE",
        "summary": "Pipeline execution completed. BRD workspace ready for interactive business analyst review."
    },
    "export_approved_document": {
        "step": 11,
        "progress": 100,
        "badge": "EXPORT",
        "summary": "Publishing verified enterprise DOCX document with full audit trail."
    }
}

class AnalysisService:
    @classmethod
    def publish_event(cls, analysis_id: str, event_data: dict[str, Any]):
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now(UTC).isoformat()
        if "analysis_id" not in event_data:
            event_data["analysis_id"] = analysis_id

        _ANALYSIS_EVENTS.setdefault(analysis_id, []).append(event_data)
        for q in list(_SUBSCRIBERS.get(analysis_id, [])):
            try:
                q.put_nowait(event_data)
            except Exception:
                pass

    @classmethod
    def subscribe(cls, analysis_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        _SUBSCRIBERS.setdefault(analysis_id, []).append(q)
        return q

    @classmethod
    def unsubscribe(cls, analysis_id: str, q: asyncio.Queue):
        if analysis_id in _SUBSCRIBERS:
            try:
                _SUBSCRIBERS[analysis_id].remove(q)
                if not _SUBSCRIBERS[analysis_id]:
                    del _SUBSCRIBERS[analysis_id]
            except ValueError:
                pass

    @classmethod
    def get_event_history(cls, analysis_id: str) -> list[dict[str, Any]]:
        return list(_ANALYSIS_EVENTS.get(analysis_id, []))

    @staticmethod
    async def start_analysis(repository_id: str, session: AsyncSession) -> AnalysisModel:
        # Check repo exists
        repo_result = await session.execute(
            select(RepositoryModel).where(RepositoryModel.id == repository_id)
        )
        repo = repo_result.scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository not found: {repository_id}")

        analysis_id = str(uuid.uuid4())
        analysis = AnalysisModel(
            id=analysis_id,
            repository_id=repository_id,
            status="scanning",
            current_node="validate_repository",
            progress_percentage=10,
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        # Publish initial pipeline kick-off event
        AnalysisService.publish_event(analysis_id, {
            "type": "step_progress",
            "node": "validate_repository",
            "step": 1,
            "total_steps": 10,
            "progress_percentage": 5,
            "status": "running",
            "message": "Analysis pipeline initiated. Preparing isolated workspace...",
            "badge": "INIT"
        })

        # Launch analysis asynchronously
        asyncio.create_task(AnalysisService._execute_workflow(analysis_id, repository_id, repo.storage_path))
        return analysis

    @staticmethod
    async def _execute_workflow(analysis_id: str, repository_id: str, storage_path: str):
        start_time = time.time()
        ANALYSIS_TOTAL.labels(status="started").inc()
        logger.info(f"Starting analysis workflow {analysis_id} on {storage_path}")

        workflow = build_analysis_workflow()
        initial_state = {
            "analysis_id": analysis_id,
            "repository_id": repository_id,
            "repo_path": storage_path,
            "errors": [],
            "current_node": "validate_repository",
        }

        # Queue to stream updates across thread boundary
        update_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _run_workflow_sync():
            try:
                for chunk in workflow.stream(initial_state, stream_mode="updates"):
                    loop.call_soon_threadsafe(update_queue.put_nowait, ("chunk", chunk))
                loop.call_soon_threadsafe(update_queue.put_nowait, ("done", None))
            except Exception as exc:
                loop.call_soon_threadsafe(update_queue.put_nowait, ("error", exc))

        loop.run_in_executor(None, _run_workflow_sync)

        final_state: dict[str, Any] = dict(initial_state)

        try:
            step_counter = 0
            while True:
                item_type, data = await update_queue.get()
                if item_type == "error":
                    raise data
                if item_type == "done":
                    break

                # chunk is {node_name: updates_dict}
                for node_name, updates in data.items():
                    final_state.update(updates)
                    step_counter += 1
                    meta = NODE_META.get(node_name, {
                        "step": step_counter,
                        "progress": min(10 + step_counter * 9, 95),
                        "badge": "AGENT",
                        "summary": f"Completed node {node_name}"
                    })

                    message = meta["summary"]
                    if node_name == "scan_source_code" and "scan_summary" in updates:
                        sum_obj = updates["scan_summary"]
                        sym_cnt = len(updates.get("discovered_symbols", []))
                        ev_cnt = len(updates.get("evidence_records", []))
                        message = f"Deterministic AST scan complete: {sum_obj.csharp_files} C# files, {sym_cnt} symbols, {ev_cnt} code anchors identified."
                    elif node_name == "extract_business_capabilities" and "business_capabilities" in updates:
                        message = f"Identified {len(updates['business_capabilities'])} core business capabilities & bounded contexts."
                    elif node_name == "generate_brd" and "brd_document" in updates:
                        brd_doc = updates["brd_document"]
                        val_res = updates.get("validation_results")
                        score_str = f" with {val_res.evidence_validation_percentage:.1f}% citation score" if val_res else ""
                        message = f"BRD document generated ({len(brd_doc.functional_requirements)} requirements, {len(brd_doc.business_rules)} rules){score_str}."

                    # Publish live SSE event
                    AnalysisService.publish_event(analysis_id, {
                        "type": "step_progress",
                        "node": node_name,
                        "step": meta.get("step", step_counter),
                        "total_steps": 10,
                        "progress_percentage": meta.get("progress", min(10 + step_counter * 9, 95)),
                        "status": "running",
                        "message": message,
                        "badge": meta.get("badge", "AGENT"),
                        "details": {
                            "node": node_name,
                            "has_errors": bool(updates.get("errors")),
                        }
                    })

                    # Update DB row so polling clients see step-by-step progress too!
                    try:
                        async with AsyncSessionLocal() as session:
                            analysis = await session.get(AnalysisModel, analysis_id)
                            if analysis:
                                analysis.current_node = node_name
                                analysis.progress_percentage = meta.get("progress", min(10 + step_counter * 9, 95))
                                analysis.status = "running"
                                await session.commit()
                    except Exception as db_err:
                        logger.warning(f"Failed to update progress in DB: {db_err}")

            duration = time.time() - start_time
            ANALYSIS_DURATION_SECONDS.observe(duration)

            # Persist to database
            async with AsyncSessionLocal() as session:
                analysis = await session.get(AnalysisModel, analysis_id)
                if not analysis:
                    return

                if final_state.get("errors"):
                    analysis.status = "failed"
                    analysis.error_message = "; ".join(final_state["errors"])
                    ANALYSIS_TOTAL.labels(status="failed").inc()
                    await session.commit()

                    AnalysisService.publish_event(analysis_id, {
                        "type": "failed",
                        "node": final_state.get("current_node", "error"),
                        "progress_percentage": 100,
                        "status": "failed",
                        "message": f"Workflow halted with errors: {analysis.error_message}",
                        "badge": "ERROR"
                    })
                    return

                # Record scan summary & validation score
                summary = final_state.get("scan_summary")
                brd: BRDDocument | None = final_state.get("brd_document")
                val_result = final_state.get("validation_results")
                score = val_result.evidence_validation_percentage if val_result else 100.0

                analysis.status = "awaiting_review"
                analysis.current_node = "await_human_review"
                analysis.progress_percentage = 100
                analysis.scan_summary = summary.model_dump() if summary else None
                analysis.validation_score = score
                analysis.completed_at = datetime.now(UTC)

                EVIDENCE_VALIDATION_SCORE.labels(analysis_id=analysis_id).set(score / 100.0)

                # Persist Evidence Records
                evidence_records = final_state.get("evidence_records", [])
                for ev in evidence_records:
                    EVIDENCE_EXTRACTED_TOTAL.labels(category=ev.category.value).inc()
                    ev_model = EvidenceModel(
                        id=ev.id,
                        analysis_id=analysis_id,
                        repository_id=repository_id,
                        relative_path=ev.relative_path,
                        symbol_name=ev.symbol_name,
                        start_line=ev.start_line,
                        end_line=ev.end_line,
                        source_excerpt=ev.source_excerpt,
                        category=ev.category.value,
                        extraction_method=ev.extraction_method,
                        validation_status=ev.validation_status,
                        metadata_json=ev.metadata
                    )
                    session.add(ev_model)

                # Persist BRD Document version
                if brd:
                    brd_version = BRDVersionModel(
                        analysis_id=analysis_id,
                        version=brd.version,
                        brd_document=brd.model_dump(),
                        review_status="PENDING"
                    )
                    session.add(brd_version)

                await session.commit()

                # Cache state for impact explorer and fast API lookups
                _ANALYSIS_CACHE[analysis_id] = {
                    "brd": brd,
                    "evidence": evidence_records,
                    "symbols": final_state.get("discovered_symbols", []),
                    "dependencies": final_state.get("dependencies", []),
                    "scan_summary": summary
                }

                ANALYSIS_TOTAL.labels(status="completed").inc()
                logger.info(f"Analysis {analysis_id} successfully completed in {duration:.2f}s with validation score {score}%")

                # Emit final completion event
                AnalysisService.publish_event(analysis_id, {
                    "type": "completed",
                    "node": "await_human_review",
                    "step": 10,
                    "total_steps": 10,
                    "progress_percentage": 100,
                    "status": "awaiting_review",
                    "message": f"Analysis complete! Ready for interactive analyst review (Score: {score:.1f}%).",
                    "badge": "COMPLETE",
                    "validation_score": score,
                })

        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed with unhandled exception: {e}", exc_info=True)
            ANALYSIS_TOTAL.labels(status="error").inc()
            async with AsyncSessionLocal() as session:
                analysis = await session.get(AnalysisModel, analysis_id)
                if analysis:
                    analysis.status = "failed"
                    analysis.error_message = str(e)
                    await session.commit()

            AnalysisService.publish_event(analysis_id, {
                "type": "failed",
                "node": "error",
                "progress_percentage": 100,
                "status": "failed",
                "message": f"Analysis failed: {str(e)}",
                "badge": "ERROR"
            })

    @staticmethod
    def get_cached_analysis_data(analysis_id: str) -> dict[str, Any] | None:
        return _ANALYSIS_CACHE.get(analysis_id)

    @staticmethod
    async def update_requirement_review(
        analysis_id: str,
        requirement_id: str,
        status: ReviewStatus,
        reviewer_name: str,
        notes: str | None,
        session: AsyncSession
    ) -> BRDDocument | None:
        cached = _ANALYSIS_CACHE.get(analysis_id)
        if not cached or not cached.get("brd"):
            # Load from DB
            brd_row = await session.execute(
                select(BRDVersionModel).where(BRDVersionModel.analysis_id == analysis_id).order_by(BRDVersionModel.version.desc())
            )
            latest = brd_row.scalars().first()
            if not latest:
                return None
            brd = BRDDocument(**latest.brd_document)
        else:
            brd = cached["brd"]

        # Update matching requirement
        for req in brd.functional_requirements:
            if req.id == requirement_id:
                req.review_status = status
                req.reviewer_notes = notes
                break

        # Record review decision
        decision = ReviewDecisionModel(
            analysis_id=analysis_id,
            requirement_id=requirement_id,
            reviewer_name=reviewer_name,
            decision=status.value,
            notes=notes
        )
        session.add(decision)

        # Save new BRD version
        brd.version += 1
        new_version_row = BRDVersionModel(
            analysis_id=analysis_id,
            version=brd.version,
            brd_document=brd.model_dump(),
            review_status=brd.review_status.value
        )
        session.add(new_version_row)
        await session.commit()

        if cached:
            cached["brd"] = brd

        return brd
