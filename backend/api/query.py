"""
KnowledgeHive - Query API

Handles user questions by orchestrating the Retrieval, Validation,
and Response agents in sequence.

Phase 3: Added Redis caching for query results. Identical questions
return cached responses instantly.
"""

import logging

from fastapi import APIRouter, Depends, Request

from backend.core.auth import require_api_key
from backend.core.rate_limit import limiter
from backend.core.dependencies import (
    get_retrieval_agent,
    get_validation_agent,
    get_response_agent,
    get_cache_manager,
)
from backend.models.query import (
    QueryRequest,
    QueryResponse,
    AgentStep,
    AgentStatus,
    Source,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
@limiter.limit("30/minute")
async def query_knowledge(
    request: Request,
    body: QueryRequest,
    _api_key: str = Depends(require_api_key),
):
    """
    Ask a question against the knowledge base.

    Pipeline:
    1. Check cache for identical query
    2. Retrieval Agent: Embed query → search Qdrant → query Neo4j
    3. Validation Agent: Score relevance → rank sources → confidence
    4. Response Agent: Generate answer with citations
    5. Cache the result for future identical queries
    """
    # Sanitize input (strip excessive whitespace)
    question = " ".join(body.question.split())
    logger.info(f"Query received: {question[:80]}...")

    # --- Check cache ---
    cache_manager = get_cache_manager()
    query_cache_key = cache_manager.make_query_key(question)

    try:
        cached = await cache_manager.get_cached_query_result(query_cache_key)
        if cached:
            logger.info("Query cache HIT — returning cached result")
            return QueryResponse(
                answer=cached["answer"],
                sources=[Source(**s) for s in cached.get("sources", [])],
                confidence=cached.get("confidence", 0.0),
                agent_flow=[
                    AgentStep(**step) for step in cached.get("agent_flow", [])
                ],
            )
    except Exception as e:
        logger.warning(f"Cache lookup failed (proceeding without cache): {e}")

    # --- Run agent pipeline ---
    agent_flow: list[AgentStep] = []

    # --- Step 1: Retrieval Agent ---
    retrieval_agent = get_retrieval_agent()
    retrieval_result = await retrieval_agent.execute({"question": question})

    agent_flow.append(
        AgentStep(
            agent_name=retrieval_agent.name,
            status=retrieval_result.status,
            duration_ms=retrieval_result.duration_ms,
            output_summary=retrieval_result.output_summary,
            error=retrieval_result.error,
        )
    )

    if retrieval_result.status == AgentStatus.FAILED:
        return QueryResponse(
            answer="Failed to retrieve relevant information. Please try again.",
            sources=[],
            confidence=0.0,
            agent_flow=agent_flow,
        )

    # --- Step 2: Validation Agent ---
    validation_agent = get_validation_agent()
    validation_result = await validation_agent.execute(
        {
            "question": question,
            "chunks": retrieval_result.output.get("chunks", []),
            "graph_context": retrieval_result.output.get("graph_context", ""),
        }
    )

    agent_flow.append(
        AgentStep(
            agent_name=validation_agent.name,
            status=validation_result.status,
            duration_ms=validation_result.duration_ms,
            output_summary=validation_result.output_summary,
            error=validation_result.error,
        )
    )

    # --- Step 3: Response Agent ---
    response_agent = get_response_agent()
    response_result = await response_agent.execute(
        {
            "question": question,
            "validated_chunks": validation_result.output.get("validated_chunks", []),
            "confidence": validation_result.output.get("confidence", 0.0),
            "graph_context": validation_result.output.get("graph_context", ""),
        }
    )

    agent_flow.append(
        AgentStep(
            agent_name=response_agent.name,
            status=response_result.status,
            duration_ms=response_result.duration_ms,
            output_summary=response_result.output_summary,
            error=response_result.error,
        )
    )

    # Build final response
    answer = response_result.output.get(
        "answer", "I could not generate an answer. Please try again."
    )
    sources_data = response_result.output.get("sources", [])
    confidence = response_result.output.get("confidence", 0.0)

    sources = [
        Source(
            document_name=s.get("document_name", "unknown"),
            chunk_text=s.get("chunk_text", ""),
            relevance_score=s.get("relevance_score", 0.0),
        )
        for s in sources_data
    ]

    # --- Cache the result ---
    try:
        cache_data = {
            "answer": answer,
            "sources": [s.model_dump() for s in sources],
            "confidence": confidence,
            "agent_flow": [step.model_dump() for step in agent_flow],
        }
        await cache_manager.cache_query_result(query_cache_key, cache_data)
        logger.info("Query result cached for future identical queries")
    except Exception as e:
        logger.warning(f"Failed to cache query result (non-critical): {e}")

    return QueryResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        agent_flow=agent_flow,
    )
