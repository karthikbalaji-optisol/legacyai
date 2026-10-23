import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.security import SecurityValidationError, validate_and_extract_zip
from backend.app.db.models import RepositoryModel


class RepositoryService:
    @staticmethod
    async def create_from_upload(upload_file: UploadFile, session: AsyncSession) -> RepositoryModel:
        repo_id = str(uuid.uuid4())
        repo_name = Path(upload_file.filename or "legacy_repo").stem

        temp_zip = settings.UPLOAD_DIR / f"{repo_id}_{upload_file.filename}"
        extract_dir = settings.REPOSITORIES_DIR / repo_id

        # Save incoming uploaded file
        total_size = 0
        with open(temp_zip, "wb") as buffer:
            while chunk := await upload_file.read(1024 * 64):
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    temp_zip.unlink(missing_ok=True)
                    raise SecurityValidationError(f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")
                buffer.write(chunk)

        # Validate and extract
        try:
            file_count, extracted_files = validate_and_extract_zip(temp_zip, extract_dir)
        finally:
            temp_zip.unlink(missing_ok=True)

        repo = RepositoryModel(
            id=repo_id,
            name=repo_name,
            source_type="zip_upload",
            file_count=file_count,
            total_size_bytes=total_size,
            storage_path=str(extract_dir)
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        return repo

    @staticmethod
    async def create_from_local_dir(dir_path: Path, session: AsyncSession, name: str = "LegacyOrders") -> RepositoryModel:
        repo_id = str(uuid.uuid4())
        extract_dir = settings.REPOSITORIES_DIR / repo_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Copy files safely
        shutil.copytree(dir_path, extract_dir, dirs_exist_ok=True)
        files = list(extract_dir.glob("**/*"))
        cs_files = [f for f in files if f.is_file()]

        repo = RepositoryModel(
            id=repo_id,
            name=name,
            source_type="local_sample",
            file_count=len(cs_files),
            total_size_bytes=sum(f.stat().st_size for f in cs_files),
            storage_path=str(extract_dir)
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        return repo
