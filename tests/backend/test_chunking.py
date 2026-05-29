"""
Tests for text chunking.
"""

import pytest
from backend.utils.chunking import chunk_text


class TestChunkText:
    """Tests for the recursive text chunker."""

    def test_basic_chunking(self, sample_text):
        """Should create non-empty chunks from text."""
        chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=200, chunk_overlap=20)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content.strip() != ""
            assert chunk.document_id == "doc-1"

    def test_chunk_ids_are_unique(self, sample_text):
        """Each chunk should have a unique ID."""
        chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=200, chunk_overlap=20)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_indices_sequential(self, sample_text):
        """Chunk indices should be sequential starting from 0."""
        chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=200, chunk_overlap=20)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_text(self):
        """Should return empty list for empty text."""
        assert chunk_text("", document_id="doc-1") == []
        assert chunk_text("   ", document_id="doc-1") == []

    def test_small_text_single_chunk(self):
        """Text smaller than chunk_size should produce one chunk."""
        text = "Hello world."
        chunks = chunk_text(text, document_id="doc-1", chunk_size=1000)
        assert len(chunks) == 1
        assert "Hello world" in chunks[0].content

    def test_chunk_metadata(self, sample_text):
        """Chunks should have metadata with char_count."""
        chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=200, chunk_overlap=20)
        for chunk in chunks:
            assert "char_count" in chunk.metadata
            assert chunk.metadata["char_count"] == len(chunk.content)

    def test_large_chunk_size_returns_fewer_chunks(self, sample_text):
        """Larger chunk size should produce fewer chunks."""
        small_chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=100)
        large_chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=1000)
        assert len(small_chunks) >= len(large_chunks)

    def test_all_text_preserved(self, sample_text):
        """All significant content should appear in at least one chunk."""
        chunks = chunk_text(sample_text, document_id="doc-1", chunk_size=200, chunk_overlap=20)
        all_content = " ".join(c.content for c in chunks)
        # Check key phrases are present
        assert "Machine Learning" in all_content
        assert "Neural" in all_content or "neural" in all_content.lower()
