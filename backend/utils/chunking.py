"""
KnowledgeHive - Text Chunking

Recursive text splitter that breaks documents into overlapping chunks
for embedding and retrieval. Inspired by LangChain's approach but
dependency-free.
"""

from backend.models.document import DocumentChunk


def chunk_text(
    text: str,
    document_id: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[DocumentChunk]:
    """
    Split text into overlapping chunks.

    Strategy:
    1. Split by double newlines (paragraphs)
    2. If a paragraph is too large, split by single newlines
    3. If still too large, split by sentences (period + space)
    4. If still too large, split by words

    Args:
        text: The full document text.
        document_id: ID of the parent document.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of DocumentChunk objects.
    """
    if not text or not text.strip():
        return []

    # Get raw segments by splitting hierarchically
    segments = _split_recursive(text, chunk_size)

    # Merge small segments and create overlapping chunks
    chunks = _merge_with_overlap(segments, chunk_size, chunk_overlap)

    # Convert to DocumentChunk objects
    return [
        DocumentChunk(
            document_id=document_id,
            content=chunk_text.strip(),
            chunk_index=i,
            metadata={"char_count": len(chunk_text.strip())},
        )
        for i, chunk_text in enumerate(chunks)
        if chunk_text.strip()
    ]


def _split_recursive(text: str, chunk_size: int) -> list[str]:
    """Recursively split text using increasingly fine separators."""
    separators = ["\n\n", "\n", ". ", " "]

    for sep in separators:
        parts = text.split(sep)
        # If splitting produced smaller parts, use them
        if len(parts) > 1 and all(len(p) <= chunk_size for p in parts):
            # Re-add separator to parts (except for the last one)
            result = []
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    result.append(part + (sep if sep != " " else " "))
                else:
                    result.append(part)
            return result

    # If text is still too large after all separators, split into segments
    # that are at most chunk_size in length
    if len(text) > chunk_size:
        parts = text.split(separators[-1])
        result = []
        for part in parts:
            if len(part) <= chunk_size:
                result.append(part + " ")
            else:
                # Hard split at chunk_size
                for i in range(0, len(part), chunk_size):
                    result.append(part[i : i + chunk_size])
        return result

    return [text]


def _merge_with_overlap(
    segments: list[str], chunk_size: int, overlap: int
) -> list[str]:
    """Merge small segments into chunks with overlap."""
    if not segments:
        return []

    chunks = []
    current_chunk = ""

    for segment in segments:
        # If adding this segment would exceed chunk_size, finalize current chunk
        if current_chunk and len(current_chunk) + len(segment) > chunk_size:
            chunks.append(current_chunk)
            # Start new chunk with overlap from end of previous chunk
            if overlap > 0 and len(current_chunk) > overlap:
                current_chunk = current_chunk[-overlap:] + segment
            else:
                current_chunk = segment
        else:
            current_chunk += segment

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks
