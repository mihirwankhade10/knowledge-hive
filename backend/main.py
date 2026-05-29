"""
KnowledgeHive - FastAPI Application Entry Point

Sets up the FastAPI app with CORS, routing, and lifecycle management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.dependencies import shutdown_services
from backend.api import upload, query, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    settings = get_settings()
    logger.info(f"🐝 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"   LLM Model: {settings.openrouter_model}")
    logger.info(f"   Embedding Model: {settings.embedding_model}")
    logger.info(f"   Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"   Neo4j: {settings.neo4j_uri}")

    yield

    # Shutdown
    logger.info("Shutting down services...")
    await shutdown_services()
    logger.info("🐝 KnowledgeHive stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Enterprise Knowledge Swarm powered by Multi-Agent AI",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # CORS - allow frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(upload.router, prefix="/api", tags=["Upload"])
    app.include_router(query.router, prefix="/api", tags=["Query"])
    app.include_router(health.router, prefix="/api", tags=["Health"])

    return app


# Application instance
app = create_app()
