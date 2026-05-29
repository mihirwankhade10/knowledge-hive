"""
KnowledgeHive - Upload API

Handles document upload, parsing, embedding, and graph extraction.
Orchestrates the Ingestion Agent and Graph Agent.
"""

import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from backend.core.config import get_settings, Settings
from backend.core.dependencies import get_ingestion_agent, get_graph_agent
from backend.models.document import UploadResponse
from backend.models.query import AgentStep, AgentStatus
from backend.utils.parsers import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a document (PDF, DOCX, or TXT).

    Pipeline:
    1. Validate file type and size
    2. Save to upload directory
    3. Run Ingestion Agent (parse → chunk → embed → store)
    4. Run Graph Agent (extract entities → store relationships)
    5. Return results
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate file size
    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {settings.max_file_size_mb}MB",
        )

    # Generate document ID and save file
    document_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{document_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved upload: {filename} -> {file_path}")

    # Run Ingestion Agent
    ingestion_agent = get_ingestion_agent()
    ingestion_result = await ingestion_agent.execute(
        {
            "file_path": str(file_path),
            "document_id": document_id,
            "filename": filename,
        }
    )

    if ingestion_result.status == AgentStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {ingestion_result.error}",
        )

    # Run Graph Agent
    graph_agent = get_graph_agent()
    graph_result = await graph_agent.execute(
        {
            "document_id": document_id,
            "chunks": ingestion_result.output.get("chunks", []),
        }
    )

    # Build response
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
