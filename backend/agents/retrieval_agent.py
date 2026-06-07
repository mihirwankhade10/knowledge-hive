"""
KnowledgeHive - Retrieval Agent

Searches Qdrant for semantically similar chunks and Neo4j for related
graph context to build a comprehensive retrieval context for answering.
"""

import logging
from typing import Optional

from backend.agents.base_agent import BaseAgent
from backend.services.embedding_service import EmbeddingProvider
from backend.services.qdrant_service import VectorStore
from backend.services.neo4j_service import GraphStore

logger = logging.getLogger(__name__)


class RetrievalAgent(BaseAgent):
    """
    Agent responsible for knowledge retrieval:
    Query → Embed → Search Qdrant → Query Neo4j → Merge Context
    """

    def __init__(
        self,
        embedding_service: EmbeddingProvider,
        vector_store: VectorStore,
        graph_store: GraphStore,
        top_k: int = 5,
    ):
        super().__init__(name="Retrieval Agent")
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.top_k = top_k

    async def _run(self, context: dict) -> dict:
        """
        Run the retrieval pipeline.

        Context requires:
            - question: str - The user's question
        """
        question = context["question"]

        # Step 1: Embed the query
        try:
            logger.info(f"[Retrieval] Embedding query: {question[:80]}...")
            query_embeddings = await self.embedding_service.embed([question])
            if not query_embeddings:
                raise ValueError("Failed to generate query embedding")
            query_vector = query_embeddings[0]
        except Exception as e:
            logger.error(f"[Retrieval] Embedding failed: {e}")
            raise

        # Step 2: Initialize vector store if needed and search Qdrant
        try:
            logger.info(f"[Retrieval] Initializing vector store...")
            dimension = self.embedding_service.get_dimension()
            await self.vector_store.initialize(dimension)
            
            logger.info(f"[Retrieval] Searching Qdrant (top_k={self.top_k})")
            search_results = await self.vector_store.search(
                query_vector=query_vector,
                limit=self.top_k,
            )
        except Exception as e:
            logger.error(f"[Retrieval] Vector search failed: {e}")
            # Return empty results instead of failing completely
            search_results = []

        # Step 3: Extract key terms for graph search
        key_terms = self._extract_key_terms(question)

        # Step 4: Query Neo4j for related entities
        try:
            logger.info(f"[Retrieval] Querying Neo4j for terms: {key_terms}")
            graph_results = await self.graph_store.query_related(key_terms)
        except Exception as e:
            logger.warning(f"[Retrieval] Graph query failed: {e}")
            graph_results = []

        # Step 5: Format results
        chunks = [
            {
                "content": result["payload"].get("content", ""),
                "filename": result["payload"].get("filename", "unknown"),
                "chunk_index": result["payload"].get("chunk_index", 0),
                "score": result["score"],
                "document_id": result["payload"].get("document_id", ""),
            }
            for result in search_results
        ]

        # Format graph context
        graph_context = self._format_graph_context(graph_results)

        # Check if we have any results
        if not chunks and not graph_context:
            logger.warning(f"[Retrieval] No results found for query: {question[:80]}...")

        return {
            "chunks": chunks,
            "graph_context": graph_context,
            "vector_results_count": len(chunks),
            "graph_results_count": len(graph_results),
        }

    def _extract_key_terms(self, question: str) -> list[str]:
        """Extract key terms from a question for graph search."""
        # Simple keyword extraction: remove stop words, keep meaningful terms
        stop_words = {
            "what", "is", "are", "how", "does", "do", "the", "a", "an",
            "in", "on", "at", "to", "for", "of", "with", "by", "from",
            "this", "that", "it", "was", "were", "be", "been", "being",
            "have", "has", "had", "can", "could", "will", "would", "should",
            "may", "might", "about", "which", "who", "whom", "when", "where",
            "why", "and", "or", "but", "not", "no", "if", "then", "than",
            "so", "up", "out", "just", "also", "very", "much", "more",
        }

        words = question.lower().replace("?", "").replace(".", "").split()
        terms = [w for w in words if w not in stop_words and len(w) > 2]
        return terms[:5]  # Limit to top 5 terms

    def _format_graph_context(self, graph_results: list[dict]) -> str:
        """Format graph results into a readable context string."""
        if not graph_results:
            return "No graph relationships found."

        lines = []
        seen = set()
        for r in graph_results:
            entity = r.get("entity", "")
            related = r.get("related_entity", "")

            if entity and entity not in seen:
                desc = r.get("entity_description", "")
                lines.append(f"- {entity} ({r.get('entity_type', 'CONCEPT')}): {desc}")
                seen.add(entity)

            if related and related not in seen:
                desc = r.get("related_description", "")
                lines.append(
                    f"- {related} ({r.get('related_type', 'CONCEPT')}): {desc}"
                    f" [related to {entity}]"
                )
                seen.add(related)

        return "\n".join(lines) if lines else "No graph relationships found."

    def _summarize(self, output: dict) -> str:
        return (
            f"Retrieved {output.get('vector_results_count', 0)} chunks, "
            f"{output.get('graph_results_count', 0)} graph entities"
        )
