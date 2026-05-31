"""
KnowledgeHive - FastAPI Application Entry Point

Sets up the FastAPI app with CORS, routing, and lifecycle management.
Phase 2: Adds structured logging, request middleware, global exception
handlers, and rate limiting.
Phase 3: Adds WebSocket router, Redis lifecycle, and Redis health check.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.core.config import get_settings
from backend.core.logging_config import setup_logging
from backend.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware
from backend.core.exceptions import register_exception_handlers, RateLimitExceededError
from backend.core.dependencies import shutdown_services, get_redis_service
from backend.core.rate_limit import limiter
from backend.api import upload, query, health
from backend.api import websocket as ws_api

# ---------------------------------------------------------------------------
# Rate limiter (Redis-backed; Phase 3)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    settings = get_settings()
    logger = logging.getLogger(__name__)
    logger.info(f"🐝 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"   LLM Model: {settings.openrouter_model}")
    logger.info(f"   Embedding Model: {settings.embedding_model}")
    logger.info(f"   Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    logger.info(f"   Neo4j: {settings.neo4j_uri}")
    logger.info(f"   Redis: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
    logger.info(f"   Auth: {'ENABLED' if settings.api_key else 'DISABLED (no API_KEY set)'}")
    logger.info(f"   Rate Limits: upload={settings.rate_limit_upload}, query={settings.rate_limit_query}")
    logger.info(f"   Cache TTL: query={settings.cache_ttl_query}s, llm={settings.cache_ttl_llm}s")

    # Initialize Redis connection at startup
    try:
        redis_service = get_redis_service()
        await redis_service.connect()
        is_connected = await redis_service.ping()
        if is_connected:
            logger.info("   ✅ Redis connected successfully")
        else:
            logger.warning("   ⚠️ Redis ping failed — caching/WS may not work")
    except Exception as e:
        logger.warning(f"   ⚠️ Redis connection failed: {e} — running without cache")

    yield

    # Shutdown
    logger.info("Shutting down services...")
    await shutdown_services()
    logger.info("🐝 KnowledgeHive stopped")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # 1. Set up structured logging FIRST (before anything else logs)
    setup_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        description="Enterprise Knowledge Swarm powered by Multi-Agent AI",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # 2. Attach the rate limiter to app state
    app.state.limiter = limiter

    # 3. Register global exception handlers (custom + validation + catch-all)
    register_exception_handlers(app)

    # 4. Handle slowapi rate-limit exceptions with our error envelope
    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request, exc):
        from starlette.responses import JSONResponse
        from backend.core.logging_config import request_id_ctx

        logger = logging.getLogger(__name__)
        logger.warning("Rate limit exceeded for %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please try again later.",
                "detail": {"limit": str(exc.detail) if hasattr(exc, 'detail') else None},
                "request_id": request_id_ctx.get("-"),
            },
        )

    # 5. Add middleware (order matters: first added = outermost)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # 6. CORS - allow frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 7. Mount routers
    app.include_router(upload.router, prefix="/api", tags=["Upload"])
    app.include_router(query.router, prefix="/api", tags=["Query"])
    app.include_router(health.router, prefix="/api", tags=["Health"])

    # 8. Mount WebSocket router (Phase 3)
    app.include_router(ws_api.router, tags=["WebSocket"])

    return app


# Application instance
app = create_app()
