"""
KnowledgeHive - Qdrant Vector Store Service

Abstracted vector store with Qdrant implementation.
Handles collection creation, vector upsert, and semantic search.
"""

import logging
from typing import Protocol, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)


class VectorStore(Protocol):
    """Protocol for vector store providers."""

    async def initialize(self, dimension: int) -> None:
        """Initialize the store (create collection if needed)."""
        ...

    async def store_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """Store vectors with metadata."""
        ...

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        ...

    async def get_collection_info(self) -> dict:
        """Get collection statistics."""
        ...


class QdrantVectorStore:
    """Vector store implementation using Qdrant."""

    def __init__(self, host: str, port: int, collection_name: str):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._client: Optional[QdrantClient] = None

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

    async def initialize(self, dimension: int) -> None:
        """Create the collection if it doesn't exist."""
        client = self._get_client()
        collections = client.get_collections().collections
        existing = [c.name for c in collections]

        if self.collection_name not in existing:
            logger.info(
                f"Creating Qdrant collection '{self.collection_name}' "
                f"with dimension {dimension}"
            )
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )
        else:
            logger.info(f"Qdrant collection '{self.collection_name}' already exists")

    async def store_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """Upsert vectors into the collection."""
        client = self._get_client()

        points = [
            PointStruct(
                id=idx,
                vector=vector,
                payload=payload,
            )
            for idx, (vector, payload) in enumerate(
                zip(vectors, payloads), start=self._get_next_id(client)
            )
        ]

        client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.info(f"Stored {len(points)} vectors in Qdrant")

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        filter_conditions: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        client = self._get_client()

        qdrant_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            qdrant_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
        ).points

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def get_collection_info(self) -> dict:
        """Get collection statistics."""
        try:
            client = self._get_client()
            info = client.get_collection(self.collection_name)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception:
            return {"vectors_count": 0, "points_count": 0, "status": "unknown"}

    def _get_next_id(self, client: QdrantClient) -> int:
        """Get the next available point ID."""
        try:
            info = client.get_collection(self.collection_name)
            return (info.points_count or 0)
        except Exception:
            return 0

    async def close(self):
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None
