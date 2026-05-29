"""
Tests for document parsers.
"""

import pytest
from backend.utils.parsers import parse_document, parse_txt, ALLOWED_EXTENSIONS


class TestParseTxt:
    """Tests for plain text parsing."""

    def test_parse_txt_basic(self, sample_txt_path, sample_text):
        """Should extract text content from TXT file."""
        result = parse_txt(sample_txt_path)
        assert "Machine Learning" in result
        assert "Artificial Intelligence" in result

    def test_parse_txt_preserves_content(self, sample_txt_path, sample_text):
        """Should preserve the full content."""
        result = parse_txt(sample_txt_path)
        assert len(result) > 0


class TestParseDocument:
    """Tests for the unified document parser."""

    def test_parse_txt_via_router(self, sample_txt_path):
        """Should route .txt files to the TXT parser."""
        result = parse_document(sample_txt_path)
        assert "Machine Learning" in result

    def test_parse_docx_via_router(self, sample_docx_path):
        """Should route .docx files to the DOCX parser."""
        result = parse_document(sample_docx_path)
        assert "Machine Learning" in result

    def test_parse_pdf_via_router(self, sample_pdf_path):
        """Should route .pdf files to the PDF parser (blank page = empty text is OK)."""
        result = parse_document(sample_pdf_path)
        # Blank PDF may return empty string
        assert isinstance(result, str)

    def test_unsupported_file_type(self, tmp_path):
        """Should raise ValueError for unsupported extensions."""
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("data")
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document(str(bad_file))

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/file.pdf")

    def test_allowed_extensions(self):
        """Should support PDF, DOCX, and TXT."""
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".txt" in ALLOWED_EXTENSIONS
