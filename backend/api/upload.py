"""
KnowledgeHive - Upload API

Handles document upload, parsing, embedding, and graph extraction.
Orchestrates the Ingestion Agent and Graph Agent.

Phase 2: Custom exceptions, MIME validation, filename sanitization,
         rate limiting, and API-key authentication.
"""

import os
import re
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, Request

from backend.core.config import get_settings, Settings
from backend.core.dependencies import get_ingestion_agent, get_graph_agent
from backend.core.auth import require_api_key
from backend.core.rate_limit import limiter
from backend.core.exceptions import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    EmptyFileError,
    InvalidMimeTypeError,
    IngestionError,
)
from backend.models.document import UploadResponse
from backend.models.query import AgentStep, AgentStatus
from backend.utils.parsers import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, validate_mime_type

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_FILENAME_RE = re.compile(r"[^\w\s\-.]", re.UNICODE)
_MAX_FILENAME_LEN = 255


def _sanitize_filename(filename: str) -> str:
    """Strip path-traversal chars and limit length."""
    # Remove any directory components
    name = Path(filename).name
    # Remove unsafe characters
    name = _SAFE_FILENAME_RE.sub("_", name)
    # Collapse runs of underscores
    name = re.sub(r"_+", "_", name).strip("_")
    # Limit length
    if len(name) > _MAX_FILENAME_LEN:
        stem = Path(name).stem[:_MAX_FILENAME_LEN - 10]
        name = stem + Path(name).suffix
    return name or "unnamed_file"


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    _api_key: str = Depends(require_api_key),
):
    """
    Upload a document (PDF, DOCX, or TXT).

    Pipeline:
    1. Validate file type, MIME type, and size
    2. Sanitize filename and save to upload directory
    3. Run Ingestion Agent (parse → chunk → embed → store)
    4. Run Graph Agent (extract entities → store relationships)
    5. Return results
    """
    # --- Validation ---

    # 1. File extension
    raw_filename = file.filename or "unknown"
    ext = Path(raw_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(ext, list(ALLOWED_EXTENSIONS))

    # 2. Read content
    content = await file.read()

    # 3. Empty file check
    if len(content) == 0:
        raise EmptyFileError()

    # 4. File size
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(len(content), settings.max_file_size_mb)

    # 5. MIME type verification (magic-byte check)
    mime_error = validate_mime_type(content, ext)
    if mime_error:
        raise InvalidMimeTypeError(
            detected=mime_error,
            expected=ALLOWED_MIME_TYPES.get(ext, []),
        )

    # --- Save file ---

    filename = _sanitize_filename(raw_filename)
    document_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{document_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved upload: {filename} → {file_path}")

    # --- Run Ingestion Agent ---
    ingestion_agent = get_ingestion_agent()
    ingestion_result = await ingestion_agent.execute(
        {
            "file_path": str(file_path),
            "document_id": document_id,
            "filename": filename,
        }
    )

    if ingestion_result.status == AgentStatus.FAILED:
        raise IngestionError(ingestion_result.error or "Unknown ingestion failure")

    # --- Run Graph Agent ---
    graph_agent = get_graph_agent()
    graph_result = await graph_agent.execute(
        {
            "document_id": document_id,
            "chunks": ingestion_result.output.get("chunks", []),
        }
    )

    # --- Build response ---
    chunks_created = ingestion_result.output.get("chunk_count", 0)
    entities_created = graph_result.output.get("entity_count", 0)
    relationships_created = graph_result.output.get("relationship_count", 0)

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        status="success",
        chunks_created=chunks_created,
        entities_created=entities_created,
        relationships_created=relationships_created,
        message=(
            f"Successfully processed '{filename}': "
            f"{chunks_created} chunks, {entities_created} entities, "
            f"{relationships_created} relationships"
        ),
    )
