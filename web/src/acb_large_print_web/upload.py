"""File upload validation and temporary directory management."""

from __future__ import annotations

import re
import shutil
import tempfile
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {".docx"}
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Base temp directory for all uploads -- set by create_app or default to system temp
UPLOAD_TEMP_BASE = Path(tempfile.gettempdir()) / "acb_lp_web"


class UploadError(Exception):
    """Raised when an uploaded file fails validation."""


def validate_upload(file: FileStorage) -> tuple[str, Path]:
    """Validate and save an uploaded file to a temporary directory.

    Args:
        file: Flask FileStorage object from request.files.

    Returns:
        Tuple of (token, saved_file_path). The token is a UUID string
        used to identify the temp directory for later download/cleanup.

    Raises:
        UploadError: If the file is missing, has a disallowed extension,
                     or has no filename.
    """
    if file is None or file.filename == "":
        raise UploadError("No file selected. Please choose a .docx file to upload.")

    filename = secure_filename(file.filename)
    if not filename:
        raise UploadError("Invalid filename.")

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(
            f"File type '{ext}' is not supported. "
            "Please upload a Microsoft Word document (.docx)."
        )

    token = str(uuid.uuid4())
    temp_dir = UPLOAD_TEMP_BASE / token
    temp_dir.mkdir(parents=True, exist_ok=True)
    saved_path = temp_dir / filename

    file.save(str(saved_path))

    # Basic magic-byte check: .docx files are ZIP archives starting with PK
    with open(saved_path, "rb") as f:
        header = f.read(4)
    if header[:2] != b"PK":
        cleanup_token(token)
        raise UploadError(
            "The uploaded file does not appear to be a valid .docx document. "
            "It may be corrupted or in a different format."
        )

    return token, saved_path


def get_temp_dir(token: str) -> Path | None:
    """Resolve a token to its temp directory path, validating the token format."""
    if not token or not _UUID_RE.match(token):
        return None
    temp_dir = UPLOAD_TEMP_BASE / token
    if not temp_dir.exists() or not temp_dir.is_dir():
        return None
    # Ensure resolved path is still under UPLOAD_TEMP_BASE (prevent traversal)
    try:
        temp_dir.resolve().relative_to(UPLOAD_TEMP_BASE.resolve())
    except ValueError:
        return None
    return temp_dir


def cleanup_token(token: str) -> None:
    """Remove the temporary directory for a given token."""
    temp_dir = get_temp_dir(token)
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)


def cleanup_tempdir(temp_dir: Path) -> None:
    """Remove a temporary directory and all its contents."""
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
