"""
KnowledgeHive - WebSocket Endpoints

Real-time communication for:
1. /ws/task/{task_id} — Upload progress tracking (Celery task updates)
2. /ws/query — Live agent status updates during query execution

Phase 3: Scalability
"""

import json
import logging
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.dependencies import (
    get_cache_manager,
    get_retrieval_agent,
    get_validation_agent,
    get_response_agent,
)
from backend.models.query import AgentStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Task Progress WebSocket (for upload tracking)
# ---------------------------------------------------------------------------

@router.websocket("/ws/task/{task_id}")
async def ws_task_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for tracking background task progress.

    Subscribes to Redis Pub/Sub channel `kh:task:{task_id}` and
    forwards all messages to the connected WebSocket client.

    The connection closes automatically when:
    - The task reaches COMPLETED or FAILED status
    - The client disconnects
    - A 5-minute timeout is reached (stale connection cleanup)
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for task: {task_id}")

    try:
        cache_manager = get_cache_manager()

        # First, send the current status (in case client connected late)
        current_status = await cache_manager.get_task_status(task_id)
        if current_status:
            await websocket.send_json(current_status)
            if current_status.get("status") in ("COMPLETED", "FAILED"):
                await websocket.close()
                return

        # Subscribe to live updates
        try:
            async for update in cache_manager.subscribe_task_updates(task_id):
                await websocket.send_json(update)

                # Close after terminal states
                if update.get("status") in ("COMPLETED", "FAILED"):
                    logger.info(f"Task {task_id} reached terminal state: {update['status']}")
                    break
        except asyncio.CancelledError:
            pass

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        try:
            await websocket.send_json({"error": str(e), "status": "ERROR"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 2. Query WebSocket (live agent status during chat queries)
# ---------------------------------------------------------------------------

@router.websocket("/ws/query")
async def ws_query(websocket: WebSocket):
    """
    WebSocket endpoint for real-time query execution.

    Client sends: {"question": "What is..."}
    Server sends intermediate updates as each agent completes:
        {"type": "agent_update", "agent": "retrieval", "status": "running"}
        {"type": "agent_update", "agent": "retrieval", "status": "completed", "duration_ms": 342}
        ...
    Final message:
        {"type": "result", "answer": "...", "sources": [...], "confidence": 0.85, "agent_flow": [...]}
    """
    await websocket.accept()
    logger.info("WebSocket query connection established")

    try:
        # Wait for the client to send a query
        data = await websocket.receive_text()
        payload = json.loads(data)
        question = payload.get("question", "").strip()

        if not question:
            await websocket.send_json({
                "type": "error",
                "message": "No question provided",
            })
            await websocket.close()
            return

        question = " ".join(question.split())  # Normalize whitespace
        logger.info(f"WebSocket query: {question[:80]}...")

        # Check cache first
        cache_manager = get_cache_manager()
        query_cache_key = cache_manager.make_query_key(question)

        try:
            cached = await cache_manager.get_cached_query_result(query_cache_key)
            if cached:
                logger.info("Query cache HIT via WebSocket")
                await websocket.send_json({
                    "type": "cache_hit",
                    "message": "Returning cached result",
                })
                await websocket.send_json({
                    "type": "result",
                    **cached,
                })
                await websocket.close()
                return
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")

        agent_flow = []

        # --- Step 1: Retrieval Agent ---
        await websocket.send_json({
            "type": "agent_update",
            "agent": "retrieval",
            "status": "running",
            "message": "Searching knowledge base...",
        })

        retrieval_agent = get_retrieval_agent()
        retrieval_result = await retrieval_agent.execute({"question": question})

        agent_flow.append({
            "agent_name": retrieval_agent.name,
            "status": retrieval_result.status,
            "duration_ms": retrieval_result.duration_ms,
            "output_summary": retrieval_result.output_summary,
        })

        await websocket.send_json({
            "type": "agent_update",
            "agent": "retrieval",
            "status": "completed" if retrieval_result.status == AgentStatus.COMPLETED else "failed",
            "duration_ms": retrieval_result.duration_ms,
            "output_summary": retrieval_result.output_summary,
        })

        if retrieval_result.status == AgentStatus.FAILED:
            await websocket.send_json({
                "type": "result",
                "answer": "Failed to retrieve relevant information. Please try again.",
                "sources": [],
                "confidence": 0.0,
                "agent_flow": agent_flow,
            })
            await websocket.close()
            return

        # --- Step 2: Validation Agent ---
        await websocket.send_json({
            "type": "agent_update",
            "agent": "validation",
            "status": "running",
            "message": "Validating evidence...",
        })

        validation_agent = get_validation_agent()
        validation_result = await validation_agent.execute({
            "question": question,
            "chunks": retrieval_result.output.get("chunks", []),
            "graph_context": retrieval_result.output.get("graph_context", ""),
        })

        agent_flow.append({
            "agent_name": validation_agent.name,
            "status": validation_result.status,
            "duration_ms": validation_result.duration_ms,
            "output_summary": validation_result.output_summary,
        })

        await websocket.send_json({
            "type": "agent_update",
            "agent": "validation",
            "status": "completed" if validation_result.status == AgentStatus.COMPLETED else "failed",
            "duration_ms": validation_result.duration_ms,
            "output_summary": validation_result.output_summary,
        })

        # --- Step 3: Response Agent ---
        await websocket.send_json({
            "type": "agent_update",
            "agent": "response",
            "status": "running",
            "message": "Generating answer...",
        })

        response_agent = get_response_agent()
        response_result = await response_agent.execute({
            "question": question,
            "validated_chunks": validation_result.output.get("validated_chunks", []),
            "confidence": validation_result.output.get("confidence", 0.0),
            "graph_context": validation_result.output.get("graph_context", ""),
        })

        agent_flow.append({
            "agent_name": response_agent.name,
            "status": response_result.status,
            "duration_ms": response_result.duration_ms,
            "output_summary": response_result.output_summary,
        })

        await websocket.send_json({
            "type": "agent_update",
            "agent": "response",
            "status": "completed" if response_result.status == AgentStatus.COMPLETED else "failed",
            "duration_ms": response_result.duration_ms,
            "output_summary": response_result.output_summary,
        })

        # --- Build and send final result ---
        answer = response_result.output.get(
            "answer", "I could not generate an answer. Please try again."
        )
        sources_data = response_result.output.get("sources", [])
        confidence = response_result.output.get("confidence", 0.0)

        sources = [
            {
                "document_name": s.get("document_name", "unknown"),
                "chunk_text": s.get("chunk_text", ""),
                "relevance_score": s.get("relevance_score", 0.0),
            }
            for s in sources_data
        ]

        final_result = {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "agent_flow": agent_flow,
        }

        # Cache the result (only if successful — don't cache error responses)
        if confidence > 0:
            try:
                await cache_manager.cache_query_result(query_cache_key, final_result)
            except Exception as e:
                logger.warning(f"Failed to cache query result: {e}")
        else:
            logger.info("Skipping cache — low/zero confidence, not caching error results")

        await websocket.send_json({
            "type": "result",
            **final_result,
        })

    except WebSocketDisconnect:
        logger.info("WebSocket query client disconnected")
    except json.JSONDecodeError:
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON payload",
            })
        except Exception:
            pass
    except Exception as e:
        logger.error(f"WebSocket query error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Query failed: {str(e)}",
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
