"""
KnowledgeHive - Document Parsers

Parse PDF, DOCX, and TXT files to extract raw text content.
Each parser is a standalone function for easy testing and extension.

Phase 2: Added MIME type mapping and magic-byte validation.
"""

import os
from pathlib import Path
from typing import Optional


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

# Mapping of extensions to expected MIME types (Phase 2)
ALLOWED_MIME_TYPES: dict[str, list[str]] = {
    ".pdf": ["application/pdf"],
    ".docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",  # DOCX is a ZIP archive internally
    ],
    ".txt": ["text/plain", "application/octet-stream"],
}

# Magic bytes for quick content verification (Phase 2)
# These are the first few bytes that identify file formats.
_MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],  # ZIP/DOCX magic bytes
}


def validate_mime_type(content: bytes, expected_ext: str) -> Optional[str]:
    """
    Verify that file content matches its claimed extension using magic bytes.

    Args:
        content: Raw file bytes.
        expected_ext: The file extension (e.g. ".pdf").

    Returns:
        None if valid, or a string describing the detected mismatch if invalid.
    """
    if not content:
        return None  # Empty file check is handled elsewhere

    signatures = _MAGIC_SIGNATURES.get(expected_ext)
    if signatures is None:
        # No magic bytes to check (e.g. .txt) — skip validation
        return None

    for sig in signatures:
        if content[:len(sig)] == sig:
            return None  # Match found — valid

    # Build a human-readable detected type description
    if content[:4] == b"%PDF":
        detected = "application/pdf"
    elif content[:4] == b"PK\x03\x04":
        detected = "application/zip (possibly docx)"
    elif content[:2] in (b"MZ", b"\x4d\x5a"):
        detected = "application/x-executable"
    elif content[:4] == b"\x89PNG":
        detected = "image/png"
    elif content[:3] == b"\xff\xd8\xff":
        detected = "image/jpeg"
    elif content[:4] == b"GIF8":
        detected = "image/gif"
    elif content[:4] == b"RIFF":
        detected = "audio/video (RIFF container)"
    else:
        detected = "unknown binary"

    return detected


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
