"""
KnowledgeHive - Document Parsers

Parse PDF, DOCX, and TXT files to extract raw text content.
Each parser is a standalone function for easy testing and extension.
"""

import os
from pathlib import Path


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document

    doc = Document(file_path)
    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text.strip())
    return "\n\n".join(text_parts)


def parse_txt(file_path: str) -> str:
    """Read a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# Map of file extensions to parser functions
_PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_txt,
}

# Allowed file extensions
ALLOWED_EXTENSIONS = set(_PARSERS.keys())


def parse_document(file_path: str) -> str:
    """
    Parse a document based on its file extension.

    Args:
        file_path: Path to the document file.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    parser = _PARSERS.get(ext)

    if parser is None:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return parser(file_path)
