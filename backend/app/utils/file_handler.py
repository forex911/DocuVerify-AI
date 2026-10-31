"""
File handling utilities: validation, hashing, safe filename generation, and storage.
"""

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

PDF_MAGIC_BYTES = b"%PDF-"


def sanitize_filename(original_filename: str) -> str:
    """
    Remove potentially dangerous characters and path traversal sequences.
    Preserves only alphanumeric characters, dashes, underscores, and dots.
    """
    base_name = os.path.basename(original_filename)
    # Remove directory separators or traversal
    safe_name = re.sub(r"[^\w\.\-]", "_", base_name)
    if not safe_name or safe_name.startswith("."):
        safe_name = f"doc_{uuid.uuid4().hex[:8]}.pdf"
    return safe_name


def generate_safe_storage_filename(original_filename: str) -> str:
    """Generate a unique, collision-proof filename for storage."""
    safe_base = sanitize_filename(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}_{safe_base}"


def calculate_sha256(file_bytes: bytes) -> str:
    """Calculate SHA-256 checksum of file contents."""
    sha = hashlib.sha256()
    sha.update(file_bytes)
    return sha.hexdigest()


async def save_uploaded_pdf(upload_file: UploadFile) -> Tuple[str, str, Path, str, int]:
    """
    Validates, hashes, and persists an uploaded PDF file safely.
    
    Returns:
        Tuple of (document_id, server_filename, file_path, sha256_hash, file_size)
    """
    original_filename = upload_file.filename or "unknown.pdf"
    safe_name = sanitize_filename(original_filename)

    # 1. Extension check
    ext = Path(safe_name).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only PDF documents (.pdf) are permitted.",
        )

    # 2. Read contents up to max size + 1 byte
    content = await upload_file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum permitted limit ({settings.MAX_UPLOAD_SIZE_BYTES} bytes).",
        )

    # 3. Magic bytes verification (PDF magic header %PDF-)
    if not content.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content header does not match valid PDF format (%PDF-).",
        )

    # 4. Hash computation
    file_hash = calculate_sha256(content)

    # 5. Safe server filename and target path
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    server_filename = f"{doc_id}_{safe_name}"
    target_path = settings.UPLOAD_DIR / server_filename

    # Prevent path traversal
    try:
        resolved_target = target_path.resolve()
        resolved_upload_dir = settings.UPLOAD_DIR.resolve()
        if not str(resolved_target).startswith(str(resolved_upload_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal attempt detected.",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination path.",
        )

    # Write file safely
    with open(target_path, "wb") as f:
        f.write(content)

    return doc_id, server_filename, target_path, file_hash, file_size

