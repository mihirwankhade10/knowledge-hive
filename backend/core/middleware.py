"""
KnowledgeHive - HTTP Middleware

RequestIdMiddleware: Generates a unique request ID per request for log correlation.
RequestLoggingMiddleware: Logs method, path, status, and duration for every request.
"""

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.core.logging_config import request_id_ctx

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Generate a unique request ID for each incoming request.

    - Stored in a ContextVar so all loggers in the request can access it.
    - Returned in the ``X-Request-ID`` response header.
    - If the client sends an ``X-Request-ID`` header, it is reused.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_ctx.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request with method, path, status code, and duration.

    Skips noisy paths like /docs, /openapi.json, and /favicon.ico.
    """

    _SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self._SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
