"""
KnowledgeHive - Pydantic Models for Queries

Data models for query requests, responses, agent flow, and sources.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgentStatus(str, Enum):
    """Status of an agent during execution."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStep(BaseModel):
    """Represents one agent's execution step in the pipeline."""

    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    duration_ms: float = 0.0
    output_summary: str = ""
    error: Optional[str] = None


class Source(BaseModel):
    """A source citation from the knowledge base."""

    document_name: str
    chunk_text: str
    relevance_score: float = 0.0


class QueryRequest(BaseModel):
    """Incoming query from the user."""

    question: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    """Full response to a user query including agent flow."""

    answer: str
    sources: list[Source] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_flow: list[AgentStep] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    qdrant: str = "unknown"
    neo4j: str = "unknown"
    redis: str = "unknown"
    version: str = "0.1.0"
