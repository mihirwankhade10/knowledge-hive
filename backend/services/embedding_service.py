"""
KnowledgeHive - Embedding Service

Abstracted embedding provider with Sentence Transformers implementation.
Lazy model loading to avoid slow startup.
"""

import logging
from typing import Protocol, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...

    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        ...


class SentenceTransformerProvider:
    """Embedding provider using sentence-transformers (runs locally)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension: Optional[int] = None

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Determine dimension from a test encoding
            test_embedding = self._model.encode(["test"])
            self._dimension = len(test_embedding[0])
            logger.info(
                f"Embedding model loaded. Dimension: {self._dimension}"
            )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Note: sentence-transformers is synchronous, but we wrap it
        for interface consistency. In production, this would run
        in a thread pool or use a GPU-accelerated async embedder.
        """
        if not texts:
            return []

        self._load_model()

        try:
            embeddings = self._model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        self._load_model()
        return self._dimension


# Future providers:
# class OpenAIEmbeddingProvider: ...
# class AzureEmbeddingProvider: ...
