"""
KnowledgeHive - Query API

Handles user questions by orchestrating the Retrieval, Validation,
and Response agents in sequence.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.core.dependencies import (
    get_retrieval_agent,
    get_validation_agent,
    get_response_agent,
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
async def query_knowledge(request: QueryRequest):
    """
    Ask a question against the knowledge base.

    Pipeline:
    1. Retrieval Agent: Embed query → search Qdrant → query Neo4j
    2. Validation Agent: Score relevance → rank sources → confidence
    3. Response Agent: Generate answer with citations
    """
    question = request.question
    logger.info(f"Query received: {question[:80]}...")

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

    return QueryResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        agent_flow=agent_flow,
    )
