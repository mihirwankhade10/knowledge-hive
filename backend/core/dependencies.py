"""
KnowledgeHive - Dependency Injection

FastAPI dependency functions for providing services and agents.
All services are created as singletons per application lifecycle.

Phase 3: Added Redis, CacheManager, and cache-aware agent factories.
"""

import logging
from functools import lru_cache

from backend.core.config import Settings, get_settings
from backend.services.llm_service import OpenRouterProvider
from backend.services.embedding_service import SentenceTransformerProvider
from backend.services.qdrant_service import QdrantVectorStore
from backend.services.neo4j_service import Neo4jGraphStore
from backend.services.redis_service import RedisService
from backend.services.cache import CacheManager
from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.graph_agent import GraphAgent
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.response_agent import ResponseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service singletons (created once, reused across requests)
# ---------------------------------------------------------------------------

_llm_service = None
_embedding_service = None
_vector_store = None
_graph_store = None
_redis_service = None
_cache_manager = None


def get_llm_service() -> OpenRouterProvider:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        settings = get_settings()
        _llm_service = OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            cache_manager=get_cache_manager(),
        )
    return _llm_service


def get_embedding_service() -> SentenceTransformerProvider:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        settings = get_settings()
        _embedding_service = SentenceTransformerProvider(
            model_name=settings.embedding_model,
        )
    return _embedding_service


def get_vector_store() -> QdrantVectorStore:
    """Get or create the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        _vector_store = QdrantVectorStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.qdrant_collection,
        )
    return _vector_store


def get_graph_store() -> Neo4jGraphStore:
    """Get or create the graph store singleton."""
    global _graph_store
    if _graph_store is None:
        settings = get_settings()
        _graph_store = Neo4jGraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
    return _graph_store


def get_redis_service() -> RedisService:
    """Get or create the Redis service singleton."""
    global _redis_service
    if _redis_service is None:
        settings = get_settings()
        _redis_service = RedisService(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
        )
    return _redis_service


def get_cache_manager() -> CacheManager:
    """Get or create the CacheManager singleton."""
    global _cache_manager
    if _cache_manager is None:
        settings = get_settings()
        _cache_manager = CacheManager(
            redis_service=get_redis_service(),
            ttl_llm=settings.cache_ttl_llm,
            ttl_query=settings.cache_ttl_query,
            ttl_entities=settings.cache_ttl_entities,
        )
    return _cache_manager


# ---------------------------------------------------------------------------
# Agent factories
# ---------------------------------------------------------------------------

def get_ingestion_agent() -> IngestionAgent:
    """Create an Ingestion Agent with injected services."""
    settings = get_settings()
    return IngestionAgent(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def get_graph_agent() -> GraphAgent:
    """Create a Graph Agent with injected services."""
    return GraphAgent(
        llm_service=get_llm_service(),
        graph_store=get_graph_store(),
    )


def get_retrieval_agent() -> RetrievalAgent:
    """Create a Retrieval Agent with injected services."""
    return RetrievalAgent(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        graph_store=get_graph_store(),
    )


def get_validation_agent() -> ValidationAgent:
    """Create a Validation Agent with injected services."""
    return ValidationAgent(
        llm_service=get_llm_service(),
    )


def get_response_agent() -> ResponseAgent:
    """Create a Response Agent with injected services."""
    return ResponseAgent(
        llm_service=get_llm_service(),
    )


async def shutdown_services():
    """Clean up all service connections on shutdown."""
    global _llm_service, _vector_store, _graph_store, _redis_service

    if _llm_service:
        await _llm_service.close()
    if _vector_store:
        await _vector_store.close()
    if _graph_store:
        await _graph_store.close()
    if _redis_service:
        await _redis_service.close()

    logger.info("All services shut down")
