"""
KnowledgeHive - Celery Tasks

Background task definitions for document ingestion.
Each task publishes progress updates via Redis Pub/Sub so
WebSocket clients can receive live status updates.

Phase 3: Scalability
"""

import asyncio
import logging
import time
from typing import Any

from backend.worker.celery_app import celery_app
from backend.core.dependencies import (
    get_ingestion_agent,
    get_graph_agent,
    get_cache_manager,
)
from backend.models.query import AgentStatus

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop (shouldn't happen in Celery),
            # create a new one in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _publish_progress(task_id: str, update: dict) -> None:
    """Publish a progress update to Redis Pub/Sub."""
    try:
        cache_manager = get_cache_manager()
        # Store latest status (for REST polling fallback)
        await cache_manager.set_task_status(task_id, update)
        # Publish to channel (for WebSocket real-time)
        await cache_manager.publish_task_update(task_id, update)
    except Exception as e:
        logger.warning(f"Failed to publish progress for task {task_id}: {e}")


@celery_app.task(
    bind=True,
    name="knowledgehive.ingest_document",
    max_retries=2,
    default_retry_delay=30,
)
def ingest_document_task(
    self,
    file_path: str,
    document_id: str,
    filename: str,
) -> dict:
    """
    Background document ingestion task.

    Pipeline:
    1. Run IngestionAgent (parse → chunk → embed → store in Qdrant)
    2. Run GraphAgent (extract entities/relationships → store in Neo4j)

    Publishes progress via Redis Pub/Sub at each step.
    """
    task_id = self.request.id
    start_time = time.time()
    logger.info(f"[Task {task_id}] Starting ingestion for '{filename}' (doc_id={document_id})")

    # --- Publish: STARTED ---
    _run_async(_publish_progress(task_id, {
        "task_id": task_id,
        "document_id": document_id,
        "filename": filename,
        "status": "STARTED",
        "step": "ingestion",
        "message": "Starting document ingestion...",
        "progress": 0,
    }))

    try:
        # ---------------------------------------------------------------
        # Step 1: Ingestion Agent
        # ---------------------------------------------------------------
        _run_async(_publish_progress(task_id, {
            "task_id": task_id,
            "document_id": document_id,
            "status": "PROCESSING",
            "step": "ingestion",
            "message": "Parsing, chunking, and embedding document...",
            "progress": 10,
        }))

        ingestion_agent = get_ingestion_agent()
        ingestion_result = _run_async(ingestion_agent.execute({
            "file_path": file_path,
            "document_id": document_id,
            "filename": filename,
        }))

        if ingestion_result.status == AgentStatus.FAILED:
            raise RuntimeError(ingestion_result.error or "Ingestion agent failed")

        chunk_count = ingestion_result.output.get("chunk_count", 0)
        chunks = ingestion_result.output.get("chunks", [])

        _run_async(_publish_progress(task_id, {
            "task_id": task_id,
            "document_id": document_id,
            "status": "PROCESSING",
            "step": "ingestion_complete",
            "message": f"Ingestion complete: {chunk_count} chunks created",
            "progress": 50,
            "chunks_created": chunk_count,
        }))

        logger.info(f"[Task {task_id}] Ingestion complete: {chunk_count} chunks")

        # ---------------------------------------------------------------
        # Step 2: Graph Agent
        # ---------------------------------------------------------------
        _run_async(_publish_progress(task_id, {
            "task_id": task_id,
            "document_id": document_id,
            "status": "PROCESSING",
            "step": "graph",
            "message": "Extracting entities and relationships...",
            "progress": 60,
        }))

        graph_agent = get_graph_agent()
        graph_result = _run_async(graph_agent.execute({
            "document_id": document_id,
            "chunks": chunks,
        }))

        entity_count = graph_result.output.get("entity_count", 0)
        relationship_count = graph_result.output.get("relationship_count", 0)

        _run_async(_publish_progress(task_id, {
            "task_id": task_id,
            "document_id": document_id,
            "status": "PROCESSING",
            "step": "graph_complete",
            "message": f"Graph extraction complete: {entity_count} entities, {relationship_count} relationships",
            "progress": 90,
            "entities_created": entity_count,
            "relationships_created": relationship_count,
        }))

        logger.info(
            f"[Task {task_id}] Graph complete: "
            f"{entity_count} entities, {relationship_count} relationships"
        )

        # ---------------------------------------------------------------
        # Complete
        # ---------------------------------------------------------------
        elapsed = round(time.time() - start_time, 2)

        result = {
            "task_id": task_id,
            "document_id": document_id,
            "filename": filename,
            "status": "COMPLETED",
            "step": "done",
            "message": (
                f"Successfully processed '{filename}': "
                f"{chunk_count} chunks, {entity_count} entities, "
                f"{relationship_count} relationships"
            ),
            "progress": 100,
            "chunks_created": chunk_count,
            "entities_created": entity_count,
            "relationships_created": relationship_count,
            "elapsed_seconds": elapsed,
        }

        _run_async(_publish_progress(task_id, result))

        # Invalidate any cached query results (new data available)
        _run_async(get_cache_manager().invalidate_document(document_id))

        logger.info(f"[Task {task_id}] Document processing completed in {elapsed}s")
        return result

    except Exception as exc:
        elapsed = round(time.time() - start_time, 2)
        error_msg = str(exc)
        logger.error(f"[Task {task_id}] Ingestion failed after {elapsed}s: {error_msg}")

        _run_async(_publish_progress(task_id, {
            "task_id": task_id,
            "document_id": document_id,
            "filename": filename,
            "status": "FAILED",
            "step": "error",
            "message": f"Processing failed: {error_msg}",
            "progress": 0,
            "error": error_msg,
            "elapsed_seconds": elapsed,
        }))

        # Retry if we haven't exceeded max_retries
        raise self.retry(exc=exc)
