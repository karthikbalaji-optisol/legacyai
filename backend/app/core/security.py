import shutil
import zipfile
from pathlib import Path
from typing import List, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger

DISALLOWED_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pfx", ".key", ".pem", ".env", ".suo"
}

IGNORED_DIRECTORIES = {
    ".git", ".vs", ".idea", ".vscode", "bin", "obj", "packages", "node_modules", "TestResults", "dist", "build"
}

class SecurityValidationError(Exception):
    pass

def validate_and_extract_zip(
    zip_path: Path,
    target_extract_dir: Path
) -> Tuple[int, List[Path]]:
    """
    Safely validates and extracts a zip file.
    Rejects:
    - Path traversal attacks (../, absolute paths)
    - Symlinks
    - Over-size limits (Zip bombs)
    - Excessive extractable file count
    - Executable/binary files
    """
    if not zip_path.exists():
        raise SecurityValidationError(f"Archive file not found: {zip_path}")

    total_size = 0
    extracted_files: List[Path] = []
    target_extract_dir.mkdir(parents=True, exist_ok=True)
    real_target_dir = target_extract_dir.resolve()

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            entries = archive.infolist()

            # 1. Absolute entry ceiling to mitigate decompression bomb DoS
            raw_entry_limit = settings.MAX_FILE_COUNT * 2
            if len(entries) > raw_entry_limit:
                raise SecurityValidationError(
                    f"Archive exceeds absolute entry ceiling ({len(entries)} > {raw_entry_limit})"
                )

            # 2. Count actual extractable candidate files (excluding directories and ignored folders)
            candidate_files = [
                e for e in entries
                if not e.is_dir() and not any(ignored in Path(e.filename).parts for ignored in IGNORED_DIRECTORIES)
            ]
            if len(candidate_files) > settings.MAX_FILE_COUNT:
                raise SecurityValidationError(
                    f"Archive exceeds maximum allowed file count ({len(candidate_files)} > {settings.MAX_FILE_COUNT})"
                )

            for entry in entries:
                # 3. Reject symlinks (UNIX symlink flag)
                if (entry.external_attr >> 16) & 0o120000 == 0o120000:
                    raise SecurityValidationError(f"Archive contains prohibited symlink entry: {entry.filename}")

                # 4. Check for path traversal
                entry_path = Path(entry.filename)
                if entry_path.is_absolute() or ".." in entry_path.parts:
                    raise SecurityValidationError(f"Malicious path traversal entry detected: {entry.filename}")

                dest_path = (target_extract_dir / entry.filename).resolve()
                if not str(dest_path).startswith(str(real_target_dir)):
                    raise SecurityValidationError(f"Extraction path escapes target sandbox: {entry.filename}")

                # Skip directories
                if entry.is_dir():
                    continue

                # 5. Skip ignored directories (.git, node_modules, packages, bin, obj, etc.)
                parts = entry_path.parts
                if any(ignored in parts for ignored in IGNORED_DIRECTORIES):
                    continue

                # 6. Check disallowed extensions
                ext = entry_path.suffix.lower()
                if ext in DISALLOWED_EXTENSIONS:
                    logger.warning(f"Ignoring dangerous/binary file in archive: {entry.filename}")
                    continue

                # 7. Check single file size & total uncompressed size limit
                if entry.file_size > settings.MAX_SINGLE_FILE_SIZE_BYTES:
                    raise SecurityValidationError(
                        f"Entry {entry.filename} exceeds max file size limit ({entry.file_size} bytes)"
                    )

                total_size += entry.file_size
                max_uncompressed = getattr(settings, "MAX_UNCOMPRESSED_SIZE_BYTES", settings.MAX_UPLOAD_SIZE_BYTES * 5)
                if total_size > max_uncompressed:
                    raise SecurityValidationError("Extracted content exceeds decompression size limit.")

                # 8. Safely extract file to sandbox
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted_files.append(dest_path)

        return len(extracted_files), extracted_files

    except zipfile.BadZipFile as e:
        raise SecurityValidationError(f"Invalid or corrupted ZIP archive: {str(e)}")

