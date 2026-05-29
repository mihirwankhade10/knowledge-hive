"""
KnowledgeHive - Pydantic Models for Documents

Data models for document upload, chunks, and metadata.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class DocumentMetadata(BaseModel):
    """Metadata associated with an uploaded document."""

    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str
    file_size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    chunk_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0
    status: str = "pending"  # pending, processing, completed, failed


class DocumentChunk(BaseModel):
    """A single chunk of a parsed document."""

    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int
    metadata: dict = Field(default_factory=dict)


class UploadResponse(BaseModel):
    """Response returned after document upload."""

    document_id: str
    filename: str
    status: str
    chunks_created: int = 0
    entities_created: int = 0
    relationships_created: int = 0
    message: str = ""


class DocumentStats(BaseModel):
    """Aggregate statistics about the knowledge base."""

    total_documents: int = 0
    total_chunks: int = 0
    total_entities: int = 0
    total_relationships: int = 0
