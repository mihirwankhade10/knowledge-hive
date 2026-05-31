"""
KnowledgeHive - Redis Service

Async Redis client wrapper with connection pooling, key-value ops,
and Pub/Sub support. Used for caching, rate-limit storage, and
real-time WebSocket message broadcasting.

Phase 3: Scalability
"""

import json
import logging
from typing import Optional, Any, AsyncIterator

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisService:
    """Async Redis client with connection pooling and Pub/Sub."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = "",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password or None
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Initialize the connection pool and client."""
        if self._client is not None:
            return

        self._pool = aioredis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            max_connections=20,
        )
        self._client = aioredis.Redis(connection_pool=self._pool)
        logger.info(f"Redis connected: {self.host}:{self.port}/{self.db}")

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Redis connection closed")

    async def _ensure_connected(self) -> aioredis.Redis:
        """Lazy-connect and return the client."""
        if self._client is None:
            await self.connect()
        return self._client  # type: ignore

    async def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            client = await self._ensure_connected()
            return await client.ping()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Key-Value Operations
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[str]:
        """Get a string value by key."""
        client = await self._ensure_connected()
        return await client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a string value with optional TTL (seconds)."""
        client = await self._ensure_connected()
        if ttl:
            await client.setex(key, ttl, value)
        else:
            await client.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        client = await self._ensure_connected()
        await client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        client = await self._ensure_connected()
        return bool(await client.exists(key))

    # ------------------------------------------------------------------
    # JSON helpers (store/retrieve Python dicts)
    # ------------------------------------------------------------------

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON-serialized value."""
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in Redis key: {key}")
            return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a JSON-serialized value."""
        await self.set(key, json.dumps(value, default=str), ttl=ttl)

    # ------------------------------------------------------------------
    # Pub/Sub (for WebSocket broadcasting)
    # ------------------------------------------------------------------

    async def publish(self, channel: str, message: dict) -> int:
        """Publish a JSON message to a Redis channel."""
        client = await self._ensure_connected()
        return await client.publish(channel, json.dumps(message, default=str))

    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        """
        Subscribe to a Redis channel and yield parsed JSON messages.

        Usage:
            async for msg in redis_service.subscribe("kh:task:abc123"):
                print(msg)
        """
        client = await self._ensure_connected()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        yield {"raw": message["data"]}
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
