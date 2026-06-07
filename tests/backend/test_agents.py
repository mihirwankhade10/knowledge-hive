"""
Tests for all agents using mocked services.
"""

import pytest
from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.graph_agent import GraphAgent
from backend.agents.retrieval_agent import RetrievalAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.response_agent import ResponseAgent
from backend.models.query import AgentStatus


@pytest.mark.asyncio
class TestIngestionAgent:
    """Tests for the Ingestion Agent."""

    async def test_successful_ingestion(
        self, sample_txt_path, mock_embedding_service, mock_vector_store
    ):
        """Should parse, chunk, embed, and store a document."""
        agent = IngestionAgent(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            chunk_size=200,
            chunk_overlap=20,
        )
        result = await agent.execute(
            {
                "file_path": sample_txt_path,
                "document_id": "test-doc-1",
                "filename": "test.txt",
            }
        )

        assert result.status == AgentStatus.COMPLETED
        assert result.output["chunk_count"] > 0
        assert result.output["document_id"] == "test-doc-1"
        assert result.duration_ms >= 0
        mock_vector_store.store_vectors.assert_called_once()

    async def test_ingestion_missing_file(
        self, mock_embedding_service, mock_vector_store
    ):
        """Should fail gracefully for missing files."""
        agent = IngestionAgent(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )
        result = await agent.execute(
            {
                "file_path": "/nonexistent/file.txt",
                "document_id": "test-doc-1",
                "filename": "missing.txt",
            }
        )

        assert result.status == AgentStatus.FAILED
        assert result.error is not None


@pytest.mark.asyncio
class TestGraphAgent:
    """Tests for the Graph Agent."""

    async def test_successful_extraction(self, mock_llm_service, mock_graph_store):
        """Should extract entities and relationships."""
        agent = GraphAgent(
            llm_service=mock_llm_service,
            graph_store=mock_graph_store,
        )

        result = await agent.execute(
            {
                "document_id": "test-doc-1",
                "chunks": [
                    {"content": "Machine Learning is a subset of AI."},
                    {"content": "Deep Learning uses neural networks."},
                ],
            }
        )

        assert result.status == AgentStatus.COMPLETED
        assert result.output["entity_count"] > 0
        mock_graph_store.store_entities.assert_called_once()

    async def test_empty_chunks(self, mock_llm_service, mock_graph_store):
        """Should handle empty chunks gracefully."""
        agent = GraphAgent(
            llm_service=mock_llm_service,
            graph_store=mock_graph_store,
        )

        result = await agent.execute(
            {"document_id": "test-doc-1", "chunks": []}
        )

        assert result.status == AgentStatus.COMPLETED
        assert result.output["entity_count"] == 0


@pytest.mark.asyncio
class TestRetrievalAgent:
    """Tests for the Retrieval Agent."""

    async def test_successful_retrieval(
        self, mock_embedding_service, mock_vector_store, mock_graph_store
    ):
        """Should retrieve relevant chunks and graph context."""
        agent = RetrievalAgent(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            graph_store=mock_graph_store,
        )

        result = await agent.execute(
            {"question": "What is Machine Learning?"}
        )

        assert result.status == AgentStatus.COMPLETED
        assert len(result.output["chunks"]) > 0
        assert result.output["graph_context"] != ""
        mock_vector_store.search.assert_called_once()


@pytest.mark.asyncio
class TestValidationAgent:
    """Tests for the Validation Agent."""

    async def test_successful_validation(self, mock_llm_service):
        """Should validate chunks and produce confidence score."""
        mock_llm_service.generate.return_value = (
            '{"relevance_scores": [0.9], "overall_confidence": 0.85, '
            '"reasoning": "Highly relevant"}'
        )

        agent = ValidationAgent(llm_service=mock_llm_service)

        result = await agent.execute(
            {
                "question": "What is ML?",
                "chunks": [
                    {
                        "content": "ML is machine learning.",
                        "filename": "test.pdf",
                        "score": 0.9,
                    }
                ],
                "graph_context": "",
            }
        )

        assert result.status == AgentStatus.COMPLETED
        assert result.output["confidence"] > 0
        assert len(result.output["validated_chunks"]) > 0

    async def test_no_chunks(self, mock_llm_service):
        """Should handle empty chunks."""
        agent = ValidationAgent(llm_service=mock_llm_service)

        result = await agent.execute(
            {"question": "What is ML?", "chunks": [], "graph_context": ""}
        )

        assert result.status == AgentStatus.COMPLETED
        assert result.output["confidence"] == 0.0


@pytest.mark.asyncio
class TestResponseAgent:
    """Tests for the Response Agent."""

    async def test_successful_response(self, mock_llm_service):
        """Should generate an answer with sources."""
        mock_llm_service.generate.return_value = (
            "Machine Learning (ML) is a subset of Artificial Intelligence "
            "that enables computers to learn from data [Source 1]."
        )

        agent = ResponseAgent(llm_service=mock_llm_service)

        result = await agent.execute(
            {
                "question": "What is ML?",
                "validated_chunks": [
                    {
                        "content": "ML is machine learning.",
                        "filename": "test.pdf",
                        "relevance_score": 0.9,
                    }
                ],
                "confidence": 0.85,
                "graph_context": "",
            }
        )

        assert result.status == AgentStatus.COMPLETED
        assert len(result.output["answer"]) > 0
        assert len(result.output["sources"]) > 0
        assert result.output["confidence"] == 0.85

    async def test_no_context(self, mock_llm_service):
        """Should return helpful message when no context available."""
        agent = ResponseAgent(llm_service=mock_llm_service)

        result = await agent.execute(
            {
                "question": "What is ML?",
                "validated_chunks": [],
                "confidence": 0.0,
                "graph_context": "",
            }
        )

        assert result.status == AgentStatus.COMPLETED
        assert "don't have enough information" in result.output["answer"]
