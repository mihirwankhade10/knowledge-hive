"""
KnowledgeHive - Health Check API

Provides health status for the backend and its dependencies.
"""

import logging

from fastapi import APIRouter

from backend.core.dependencies import get_vector_store, get_graph_store
from backend.models.query import HealthResponse
from backend.models.document import DocumentStats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of backend and all connected services."""
    qdrant_status = "unhealthy"
    neo4j_status = "unhealthy"

    # Check Qdrant
    try:
        vector_store = get_vector_store()
        info = await vector_store.get_collection_info()
        qdrant_status = "healthy"
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")

    # Check Neo4j
    try:
        graph_store = get_graph_store()
        stats = await graph_store.get_stats()
        neo4j_status = "healthy"
    except Exception as e:
        logger.warning(f"Neo4j health check failed: {e}")

    overall = "healthy" if qdrant_status == "healthy" and neo4j_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall,
        qdrant=qdrant_status,
        neo4j=neo4j_status,
    )


@router.get("/stats", response_model=DocumentStats)
async def get_stats():
    """Get knowledge base statistics."""
    try:
        vector_store = get_vector_store()
        qdrant_info = await vector_store.get_collection_info()

        graph_store = get_graph_store()
        graph_stats = await graph_store.get_stats()

        return DocumentStats(
            total_documents=graph_stats.get("document_count", 0),
            total_chunks=qdrant_info.get("points_count", 0),
            total_entities=graph_stats.get("entity_count", 0),
            total_relationships=graph_stats.get("relationship_count", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return DocumentStats()
