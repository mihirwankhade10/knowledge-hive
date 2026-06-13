"""
KnowledgeHive - Application Configuration

Centralized settings loaded from environment variables via pydantic-settings.
All configuration is validated at startup.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_name: str = "KnowledgeHive"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- LLM Provider (OpenRouter) ---
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="OpenRouter model identifier",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )

    # --- Embedding Model ---
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence Transformers model name",
    )

    # --- Qdrant ---
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection: str = Field(
        default="knowledge_hive", description="Qdrant collection name"
    )

    # --- Neo4j ---
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="knowledgehive", description="Neo4j password")

    # --- Upload ---
    upload_dir: str = Field(default="./uploads", description="Upload directory path")
    max_file_size_mb: int = Field(default=50, description="Max upload file size in MB")

    # --- Chunking ---
    chunk_size: int = Field(default=512, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Chunk overlap in characters")

    # --- Authentication (Phase 2) ---
    api_key: str = Field(
        default="", description="API key for protected endpoints. Empty = auth disabled."
    )

    # --- Rate Limiting (Phase 2) ---
    rate_limit_upload: str = Field(default="10/minute", description="Rate limit for upload endpoint")
    rate_limit_query: str = Field(default="30/minute", description="Rate limit for query endpoint")
    rate_limit_health: str = Field(default="60/minute", description="Rate limit for health endpoints")

    # --- Server ---
    backend_host: str = Field(default="0.0.0.0", description="Backend host")
    backend_port: int = Field(default=8000, description="Backend port")

    # --- Frontend ---
    vite_api_url: str = Field(default="http://localhost:8000", description="Frontend API URL")

    # --- Redis (Phase 3) ---
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: str = Field(default="", description="Redis password (empty = no auth)")

    # --- Cache TTL (Phase 3) ---
    cache_ttl_query: int = Field(default=3600, description="Query result cache TTL in seconds")
    cache_ttl_llm: int = Field(default=3600, description="LLM response cache TTL in seconds")
    cache_ttl_entities: int = Field(default=86400, description="Entity extraction cache TTL in seconds")

    # --- Celery (Phase 3) ---
    celery_broker_url: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", description="Celery result backend URL")
    celery_worker_concurrency: int = Field(default=2, description="Celery worker concurrency")

    # --- Observability: Langfuse (Phase 4) ---
    langfuse_public_key: str = Field(default="", description="Langfuse Public Key")
    langfuse_secret_key: str = Field(default="", description="Langfuse Secret Key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse Host URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance - loaded once per process."""
    return Settings()
