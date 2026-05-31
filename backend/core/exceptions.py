"""
KnowledgeHive - Custom Exceptions & Global Error Handlers

Provides:
- A hierarchy of custom exceptions for known error conditions.
- A standardized ``ErrorResponse`` envelope for all error responses.
- Global exception handlers that are registered on the FastAPI app.
"""

import logging
import traceback
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from backend.core.logging_config import request_id_ctx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardized error response envelope
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """JSON envelope returned for every error."""

    error: str                    # Machine-readable code (e.g. "validation_error")
    message: str                  # Human-readable description
    detail: Optional[Any] = None  # Extra context (field errors, etc.)
    request_id: str = ""          # Correlation ID


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class KnowledgeHiveError(Exception):
    """Base exception for all KnowledgeHive-specific errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = "An internal error occurred", detail: Any = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class UnsupportedFileTypeError(KnowledgeHiveError):
    status_code = 400
    error_code = "unsupported_file_type"

    def __init__(self, ext: str, allowed: list[str]):
        super().__init__(
            message=f"Unsupported file type: '{ext}'. Supported: {', '.join(allowed)}",
            detail={"extension": ext, "allowed": allowed},
        )


class FileTooLargeError(KnowledgeHiveError):
    status_code = 413
    error_code = "file_too_large"

    def __init__(self, size_bytes: int, max_mb: int):
        super().__init__(
            message=f"File too large ({size_bytes / 1_048_576:.1f}MB). Maximum: {max_mb}MB",
            detail={"size_bytes": size_bytes, "max_mb": max_mb},
        )


class EmptyFileError(KnowledgeHiveError):
    status_code = 400
    error_code = "empty_file"

    def __init__(self):
        super().__init__(message="Uploaded file is empty (0 bytes)")


class InvalidMimeTypeError(KnowledgeHiveError):
    status_code = 400
    error_code = "invalid_mime_type"

    def __init__(self, detected: str, expected: list[str]):
        super().__init__(
            message=f"File content does not match its extension. Detected: '{detected}'",
            detail={"detected_mime": detected, "expected_mimes": expected},
        )


class DocumentNotFoundError(KnowledgeHiveError):
    status_code = 404
    error_code = "document_not_found"

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            detail={"document_id": document_id},
        )


class ServiceUnavailableError(KnowledgeHiveError):
    status_code = 503
    error_code = "service_unavailable"

    def __init__(self, service_name: str, reason: str = ""):
        msg = f"Service unavailable: {service_name}"
        if reason:
            msg += f" ({reason})"
        super().__init__(message=msg, detail={"service": service_name})


class AuthenticationError(KnowledgeHiveError):
    status_code = 401
    error_code = "authentication_error"

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message=message)


class RateLimitExceededError(KnowledgeHiveError):
    status_code = 429
    error_code = "rate_limit_exceeded"

    def __init__(self, limit: str = ""):
        msg = "Rate limit exceeded. Please try again later."
        if limit:
            msg += f" Limit: {limit}"
        super().__init__(message=msg, detail={"limit": limit})


class IngestionError(KnowledgeHiveError):
    status_code = 500
    error_code = "ingestion_error"

    def __init__(self, reason: str):
        super().__init__(message=f"Ingestion failed: {reason}")


# ---------------------------------------------------------------------------
# Helper to build the envelope
# ---------------------------------------------------------------------------

def _build_error_response(
    error_code: str, message: str, detail: Any = None
) -> dict:
    return ErrorResponse(
        error=error_code,
        message=message,
        detail=detail,
        request_id=request_id_ctx.get("-"),
    ).model_dump()


# ---------------------------------------------------------------------------
# Global exception handler registration
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""

    @app.exception_handler(KnowledgeHiveError)
    async def _handle_knowledgehive_error(request: Request, exc: KnowledgeHiveError):
        from starlette.responses import JSONResponse

        logger.warning("KnowledgeHiveError [%s]: %s", exc.error_code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_response(exc.error_code, exc.message, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError):
        from starlette.responses import JSONResponse

        errors = exc.errors()
        logger.warning("Validation error: %s", errors)
        return JSONResponse(
            status_code=422,
            content=_build_error_response(
                "validation_error",
                "Request validation failed",
                detail=[
                    {
                        "field": " → ".join(str(loc) for loc in e.get("loc", [])),
                        "message": e.get("msg", ""),
                        "type": e.get("type", ""),
                    }
                    for e in errors
                ],
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unhandled_error(request: Request, exc: Exception):
        from starlette.responses import JSONResponse

        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        # Hide internals from the client
        return JSONResponse(
            status_code=500,
            content=_build_error_response(
                "internal_error",
                "An unexpected error occurred. Please try again later.",
            ),
        )
