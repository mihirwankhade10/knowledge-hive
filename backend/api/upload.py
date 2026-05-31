"""
KnowledgeHive - Upload API

Handles document upload and validation. Queues ingestion as a
background Celery task instead of blocking the HTTP request.

Phase 3: Async upload via Celery, task status polling endpoint,
         plus a sync fallback for environments without Celery.
"""

import os
import re
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, Request, Query

from backend.core.config import get_settings, Settings
from backend.core.dependencies import get_ingestion_agent, get_graph_agent, get_cache_manager
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


def _is_celery_available() -> bool:
    """Check if Celery workers are reachable (Redis broker is up)."""
    try:
        from backend.worker.celery_app import celery_app
        # Quick ping to the broker
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Upload endpoint (Phase 3: async via Celery)
# ---------------------------------------------------------------------------

@router.post("/upload", status_code=202)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    _api_key: str = Depends(require_api_key),
    sync: bool = Query(False, description="Force synchronous processing (skip Celery)"),
):
    """
    Upload a document (PDF, DOCX, or TXT).

    Phase 3 behavior:
    - Returns 202 Accepted immediately with a task_id
    - Actual ingestion happens in a Celery background worker
    - Track progress via WebSocket: ws://host/ws/task/{task_id}
    - Or poll via REST: GET /api/upload/status/{task_id}

    Set ?sync=true to force synchronous processing (Phase 1/2 behavior).
    """
    # --- Validation (same as Phase 2) ---

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

    # --- Async processing via Celery (default) ---

    if not sync and _is_celery_available():
        from backend.worker.tasks import ingest_document_task

        task = ingest_document_task.delay(
            str(file_path),
            document_id,
            filename,
        )

        logger.info(f"Enqueued ingestion task: {task.id} for doc {document_id}")

        return {
            "task_id": task.id,
            "document_id": document_id,
            "filename": filename,
            "status": "accepted",
            "message": "Document queued for processing. Connect to WebSocket for progress.",
            "ws_url": f"/ws/task/{task.id}",
        }

    # --- Sync fallback (Celery not available or ?sync=true) ---

    logger.info("Processing upload synchronously (Celery not available or sync=true)")

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

    graph_agent = get_graph_agent()
    graph_result = await graph_agent.execute(
        {
            "document_id": document_id,
            "chunks": ingestion_result.output.get("chunks", []),
        }
    )

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


# ---------------------------------------------------------------------------
# Task status endpoint (REST fallback for non-WebSocket clients)
# ---------------------------------------------------------------------------

@router.get("/upload/status/{task_id}")
@limiter.limit("60/minute")
async def get_task_status(request: Request, task_id: str):
    """
    Check the status of a background ingestion task.

    Returns the latest status from Redis (fast) and Celery result backend.
    """
    # Try Redis cache first (contains step-by-step progress)
    try:
        cache_manager = get_cache_manager()
        cached_status = await cache_manager.get_task_status(task_id)
        if cached_status:
            return cached_status
    except Exception as e:
        logger.warning(f"Redis status lookup failed: {e}")

    # Fall back to Celery result backend
    try:
        from backend.worker.celery_app import celery_app
        from celery.result import AsyncResult

        result = AsyncResult(task_id, app=celery_app)
        response = {
            "task_id": task_id,
            "status": result.status,
            "progress": 100 if result.ready() else 0,
        }
        if result.ready():
            response["result"] = result.result
        if result.failed():
            response["error"] = str(result.result)
        return response
    except Exception as e:
        logger.error(f"Task status lookup failed: {e}")
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "message": "Could not determine task status",
        }
