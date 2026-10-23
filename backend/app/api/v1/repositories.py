from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import SecurityValidationError
from backend.app.db.database import get_db_session
from backend.app.schemas.api import RepositoryCreateResponse
from backend.app.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["Repositories"])

@router.post("", response_model=RepositoryCreateResponse, status_code=status.HTTP_201_CREATED)
async def upload_repository(
    file: Optional[UploadFile] = File(None),
    use_sample: bool = Form(False),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Upload a legacy .NET repository ZIP archive or initialize with the built-in LegacyOrders sample.
    Safe extraction with path traversal protection, symlink rejection, and file size limits.
    """
    if use_sample or file is None:
        sample_path = settings.BASE_DIR / "samples" / "LegacyOrders"
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="LegacyOrders sample repository not found.")
        repo = await RepositoryService.create_from_local_dir(sample_path, session, name="LegacyOrders (.NET 8.0)")
        return RepositoryCreateResponse(
            repository_id=repo.id,
            name=repo.name,
            file_count=repo.file_count,
            total_size_bytes=repo.total_size_bytes,
            created_at=repo.created_at.isoformat()
        )

    try:
        repo = await RepositoryService.create_from_upload(file, session)
        return RepositoryCreateResponse(
            repository_id=repo.id,
            name=repo.name,
            file_count=repo.file_count,
            total_size_bytes=repo.total_size_bytes,
            created_at=repo.created_at.isoformat()
        )
    except SecurityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")
