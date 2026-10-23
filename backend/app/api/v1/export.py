import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db_session
from backend.app.db.models import ExportModel
from backend.app.schemas.brd import BRDDocument
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.docx_export_service import DocxExportService

router = APIRouter(prefix="", tags=["Export"])

@router.post("/analyses/{analysis_id}/export")
async def export_brd(
    analysis_id: str,
    export_format: str = "docx",
    session: AsyncSession = Depends(get_db_session)
):
    if export_format != "docx":
        raise HTTPException(status_code=400, detail="Only 'docx' export is currently supported.")

    cached = AnalysisService.get_cached_analysis_data(analysis_id)
    if not cached or not cached.get("brd"):
        raise HTTPException(status_code=404, detail="Analysis BRD not ready for export.")

    brd: BRDDocument = cached["brd"]
    out_file = DocxExportService.generate_docx(brd)

    export_id = str(uuid.uuid4())
    export_record = ExportModel(
        id=export_id,
        analysis_id=analysis_id,
        export_format="docx",
        file_path=str(out_file)
    )
    session.add(export_record)
    await session.commit()

    return {
        "export_id": export_id,
        "analysis_id": analysis_id,
        "format": "docx",
        "download_url": f"/api/v1/exports/{export_id}/download",
        "filename": out_file.name
    }

@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    export_record = await session.get(ExportModel, export_id)
    if not export_record:
        raise HTTPException(status_code=404, detail="Export not found.")

    file_path = Path(export_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file missing from disk.")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=file_path.name
    )

