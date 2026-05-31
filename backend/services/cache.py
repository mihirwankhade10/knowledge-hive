"""
KnowledgeHive - Cache Manager

Higher-level caching utilities built on top of RedisService.
Provides typed caching for LLM responses, query results, and
document-level cache invalidation.

Phase 3: Scalability
"""

import hashlib
import json
import logging
from typing import Optional, Any

from backend.services.redis_service import RedisService

logger = logging.getLogger(__name__)

# Key prefixes for namespace isolation
_PREFIX_LLM = "kh:llm"
_PREFIX_QUERY = "kh:query"
_PREFIX_TASK = "kh:task"
_PREFIX_DOC = "kh:doc"


class CacheManager:
    """
    Application-level cache manager.

    Wraps RedisService with domain-specific caching logic
    for LLM responses, full query pipeline results, and
    Celery task metadata.
    """

    def __init__(
        self,
        redis_service: RedisService,
        ttl_llm: int = 3600,
        ttl_query: int = 3600,
        ttl_entities: int = 86400,
    ):
        self.redis = redis_service
        self.ttl_llm = ttl_llm
        self.ttl_query = ttl_query
        self.ttl_entities = ttl_entities

    # ------------------------------------------------------------------
    # Hash helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(text: str) -> str:
        """Create a SHA-256 hash of a string (deterministic cache key)."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

    def make_llm_key(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "",
    ) -> str:
        """Generate a cache key for an LLM call."""
        raw = f"{model}|{system_prompt or ''}|{prompt}"
        return f"{_PREFIX_LLM}:{self._hash(raw)}"

    def make_query_key(self, question: str) -> str:
        """Generate a cache key for a full query pipeline result."""
        normalized = " ".join(question.lower().split())
        return f"{_PREFIX_QUERY}:{self._hash(normalized)}"

    # ------------------------------------------------------------------
    # LLM response caching
    # ------------------------------------------------------------------

    async def get_cached_llm_response(self, cache_key: str) -> Optional[str]:
        """Retrieve a cached LLM response."""
        result = await self.redis.get(cache_key)
        if result is not None:
            logger.debug(f"Cache HIT: {cache_key}")
        return result

    async def cache_llm_response(self, cache_key: str, response: str) -> None:
        """Store an LLM response in cache."""
        await self.redis.set(cache_key, response, ttl=self.ttl_llm)
        logger.debug(f"Cache SET: {cache_key} (ttl={self.ttl_llm}s)")

    # ------------------------------------------------------------------
    # Full query result caching
    # ------------------------------------------------------------------

    async def get_cached_query_result(self, cache_key: str) -> Optional[dict]:
        """Retrieve a cached query pipeline result."""
        result = await self.redis.get_json(cache_key)
        if result is not None:
            logger.debug(f"Query cache HIT: {cache_key}")
        return result

    async def cache_query_result(self, cache_key: str, result: dict) -> None:
        """Store a full query pipeline result in cache."""
        await self.redis.set_json(cache_key, result, ttl=self.ttl_query)
        logger.debug(f"Query cache SET: {cache_key} (ttl={self.ttl_query}s)")

    # ------------------------------------------------------------------
    # Task status (for Celery background ingestion)
    # ------------------------------------------------------------------

    async def set_task_status(self, task_id: str, status: dict) -> None:
        """Store the latest status for a background task."""
        key = f"{_PREFIX_TASK}:{task_id}"
        await self.redis.set_json(key, status, ttl=3600)

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get the latest status for a background task."""
        key = f"{_PREFIX_TASK}:{task_id}"
        return await self.redis.get_json(key)

    # ------------------------------------------------------------------
    # Document-level invalidation
    # ------------------------------------------------------------------

    async def invalidate_document(self, document_id: str) -> None:
        """
        Invalidate all cache entries associated with a document.

        Called when a document is re-uploaded or deleted, so stale
        query results referencing that document are cleared.
        """
        # Track which queries reference which documents
        doc_key = f"{_PREFIX_DOC}:{document_id}:queries"
        query_keys = await self.redis.get_json(doc_key)

        if query_keys and isinstance(query_keys, list):
            for qk in query_keys:
                await self.redis.delete(qk)
            logger.info(
                f"Invalidated {len(query_keys)} cached queries for doc {document_id}"
            )

        await self.redis.delete(doc_key)

    async def track_query_for_document(
        self, document_id: str, query_cache_key: str
    ) -> None:
        """
        Associate a query cache key with a document for later invalidation.
        """
        doc_key = f"{_PREFIX_DOC}:{document_id}:queries"
        existing = await self.redis.get_json(doc_key) or []
        if query_cache_key not in existing:
            existing.append(query_cache_key)
        await self.redis.set_json(doc_key, existing, ttl=self.ttl_query)

    # ------------------------------------------------------------------
    # Pub/Sub passthrough (for WebSocket integration)
    # ------------------------------------------------------------------

    async def publish_task_update(self, task_id: str, update: dict) -> None:
        """Publish a progress update for a background task."""
        channel = f"{_PREFIX_TASK}:{task_id}"
        await self.redis.publish(channel, update)

    async def subscribe_task_updates(self, task_id: str):
        """Subscribe to progress updates for a background task."""
        channel = f"{_PREFIX_TASK}:{task_id}"
        async for message in self.redis.subscribe(channel):
            yield message
