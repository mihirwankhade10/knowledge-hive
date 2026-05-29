"""
Shared pytest fixtures for KnowledgeHive backend tests.
"""

import os
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def sample_text():
    """Sample document text for testing."""
    return (
        "Machine Learning is a subset of Artificial Intelligence. "
        "It enables computers to learn from data without being explicitly programmed. "
        "Deep Learning is a type of Machine Learning that uses neural networks.\n\n"
        "Natural Language Processing (NLP) is another important area of AI. "
        "NLP focuses on the interaction between computers and human language. "
        "Transformers are a key architecture used in modern NLP models.\n\n"
        "Companies like Google, OpenAI, and Microsoft are leading AI research. "
        "They develop large language models that can understand and generate text."
    )


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file for testing."""
    from PyPDF2 import PdfWriter

    pdf_path = tmp_path / "test_document.pdf"
    writer = PdfWriter()
    # PyPDF2 can create a basic PDF with a blank page
    writer.add_blank_page(width=612, height=792)
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return str(pdf_path)


@pytest.fixture
def sample_txt_path(tmp_path, sample_text):
    """Create a sample TXT file for testing."""
    txt_path = tmp_path / "test_document.txt"
    txt_path.write_text(sample_text, encoding="utf-8")
    return str(txt_path)


@pytest.fixture
def sample_docx_path(tmp_path, sample_text):
    """Create a sample DOCX file for testing."""
    from docx import Document

    docx_path = tmp_path / "test_document.docx"
    doc = Document()
    for paragraph in sample_text.split("\n\n"):
        doc.add_paragraph(paragraph)
    doc.save(str(docx_path))
    return str(docx_path)


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing without API calls."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value='[{"name": "Machine Learning", "type": "CONCEPT", "description": "A subset of AI"}]')
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing without model loading."""
    mock = MagicMock()
    mock.embed = AsyncMock(return_value=[[0.1] * 384])
    mock.get_dimension = MagicMock(return_value=384)
    return mock


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing without Qdrant."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.store_vectors = AsyncMock()
    mock.search = AsyncMock(
        return_value=[
            {
                "id": "1",
                "score": 0.85,
                "payload": {
                    "content": "Machine Learning is a subset of AI.",
                    "filename": "test.pdf",
                    "document_id": "doc-1",
                    "chunk_index": 0,
                },
            }
        ]
    )
    mock.get_collection_info = AsyncMock(
        return_value={"vectors_count": 10, "points_count": 10, "status": "green"}
    )
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_graph_store():
    """Mock graph store for testing without Neo4j."""
    mock = AsyncMock()
    mock.initialize = AsyncMock()
    mock.store_entities = AsyncMock(return_value=3)
    mock.store_relationships = AsyncMock(return_value=2)
    mock.query_related = AsyncMock(
        return_value=[
            {
                "entity": "Machine Learning",
                "entity_type": "CONCEPT",
                "entity_description": "A subset of AI",
                "related_entity": "AI",
                "related_type": "CONCEPT",
                "related_description": "Artificial Intelligence",
            }
        ]
    )
    mock.get_stats = AsyncMock(
        return_value={"entity_count": 5, "relationship_count": 3, "document_count": 1}
    )
    mock.close = AsyncMock()
    return mock
