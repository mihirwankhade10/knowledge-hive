"""
KnowledgeHive - Ingestion Agent

Parses documents, chunks text, generates embeddings, and stores vectors in Qdrant.
This is the first agent in the upload pipeline.
"""

import logging

from backend.agents.base_agent import BaseAgent
from backend.utils.parsers import parse_document
from backend.utils.chunking import chunk_text
from backend.services.embedding_service import EmbeddingProvider
from backend.services.qdrant_service import VectorStore

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """
    Agent responsible for document ingestion pipeline:
    Parse → Chunk → Embed → Store in Qdrant
    """

    def __init__(
        self,
        embedding_service: EmbeddingProvider,
        vector_store: VectorStore,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        super().__init__(name="Ingestion Agent")
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def _run(self, context: dict) -> dict:
        """
        Run the ingestion pipeline.

        Context requires:
            - file_path: str - Path to the uploaded file
            - document_id: str - Unique document ID
            - filename: str - Original filename
        """
        file_path = context["file_path"]
        document_id = context["document_id"]
        filename = context.get("filename", "unknown")

        # Step 1: Parse document
        logger.info(f"[Ingestion] Parsing: {filename}")
        raw_text = parse_document(file_path)

        if not raw_text.strip():
            raise ValueError(f"No text extracted from {filename}")

        # Step 2: Chunk text
        logger.info(f"[Ingestion] Chunking text ({len(raw_text)} chars)")
        chunks = chunk_text(
            text=raw_text,
            document_id=document_id,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        if not chunks:
            raise ValueError(f"No chunks created from {filename}")

        # Step 3: Generate embeddings
        logger.info(f"[Ingestion] Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [c.content for c in chunks]
        embeddings = await self.embedding_service.embed(chunk_texts)

        # Step 4: Initialize vector store if needed
        dimension = self.embedding_service.get_dimension()
        await self.vector_store.initialize(dimension)

        # Step 5: Store in Qdrant
        logger.info(f"[Ingestion] Storing {len(chunks)} vectors in Qdrant")
        ids = [c.chunk_id for c in chunks]
        payloads = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "char_count": len(c.content),
            }
            for c in chunks
        ]

        await self.vector_store.store_vectors(
            ids=ids,
            vectors=embeddings,
            payloads=payloads,
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "text_length": len(raw_text),
            "chunk_count": len(chunks),
            "chunks": [
                {"chunk_id": c.chunk_id, "content": c.content[:100]}
                for c in chunks
            ],
        }

    def _summarize(self, output: dict) -> str:
        return (
            f"Parsed '{output.get('filename', '?')}': "
            f"{output.get('chunk_count', 0)} chunks, "
            f"{output.get('text_length', 0)} chars"
        )
