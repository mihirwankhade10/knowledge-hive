"""
Tests for API endpoints.

Uses FastAPI TestClient with mocked dependencies.
"""

import io
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        with patch("backend.api.health.get_vector_store") as mock_vs, \
             patch("backend.api.health.get_graph_store") as mock_gs:
            mock_vs.return_value.get_collection_info = AsyncMock(return_value={})
            mock_gs.return_value.get_stats = AsyncMock(return_value={})

            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "qdrant" in data
            assert "neo4j" in data


class TestUploadEndpoint:
    """Tests for POST /api/upload."""

    def test_upload_rejects_unsupported_type(self, client):
        """Should reject files with unsupported extensions."""
        file_content = b"test content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.xyz", io.BytesIO(file_content), "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["message"]

    def test_upload_accepts_txt(self, client):
        """Should accept TXT files (mocked pipeline)."""
        with patch("backend.api.upload.get_ingestion_agent") as mock_ia, \
             patch("backend.api.upload.get_graph_agent") as mock_ga:

            # Mock ingestion agent
            mock_ingestion = MagicMock()
            mock_ingestion.execute = AsyncMock(return_value=MagicMock(
                status="completed",
                output={"chunk_count": 3, "chunks": []},
                error=None,
            ))
            mock_ia.return_value = mock_ingestion

            # Mock graph agent
            mock_graph = MagicMock()
            mock_graph.execute = AsyncMock(return_value=MagicMock(
                status="completed",
                output={"entity_count": 2, "relationship_count": 1},
                error=None,
            ))
            mock_ga.return_value = mock_graph

            file_content = b"Machine Learning is a subset of AI."
            response = client.post(
                "/api/upload",
                files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            )
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "accepted"
            assert "document_id" in data


class TestQueryEndpoint:
    """Tests for POST /api/query."""

    def test_query_requires_question(self, client):
        """Should reject empty questions."""
        response = client.post("/api/query", json={"question": ""})
        assert response.status_code == 422  # Validation error

    def test_query_success(self, client):
        """Should return answer with sources (mocked agents)."""
        with patch("backend.api.query.get_retrieval_agent") as mock_ra, \
             patch("backend.api.query.get_validation_agent") as mock_va, \
             patch("backend.api.query.get_response_agent") as mock_resp:

            # Mock retrieval
            mock_retrieval = MagicMock()
            mock_retrieval.name = "Retrieval Agent"
            mock_retrieval.execute = AsyncMock(return_value=MagicMock(
                status="completed",
                output={"chunks": [{"content": "ML is AI", "filename": "t.pdf", "score": 0.9}], "graph_context": ""},
                output_summary="Retrieved 1 chunk",
                duration_ms=100.0,
                error=None,
            ))
            mock_ra.return_value = mock_retrieval

            # Mock validation
            mock_validation = MagicMock()
            mock_validation.name = "Validation Agent"
            mock_validation.execute = AsyncMock(return_value=MagicMock(
                status="completed",
                output={"validated_chunks": [{"content": "ML is AI", "filename": "t.pdf", "relevance_score": 0.9}], "confidence": 0.85, "graph_context": ""},
                output_summary="Validated 1 chunk",
                duration_ms=200.0,
                error=None,
            ))
            mock_va.return_value = mock_validation

            # Mock response
            mock_response = MagicMock()
            mock_response.name = "Response Agent"
            mock_response.execute = AsyncMock(return_value=MagicMock(
                status="completed",
                output={"answer": "ML is a subset of AI.", "sources": [{"document_name": "t.pdf", "chunk_text": "ML is AI", "relevance_score": 0.9}], "confidence": 0.85},
                output_summary="Generated answer",
                duration_ms=500.0,
                error=None,
            ))
            mock_resp.return_value = mock_response

            response = client.post("/api/query", json={"question": "What is ML?"})
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "confidence" in data
            assert "agent_flow" in data
            assert len(data["agent_flow"]) == 3
