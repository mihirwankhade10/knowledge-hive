"""
KnowledgeHive - API Key Authentication

Lightweight API-key authentication via the ``X-API-Key`` header.

- If the ``API_KEY`` setting is empty, auth is **disabled** (backward-compatible
  for local development).
- If set, every protected endpoint must include the header.
"""

import logging
from typing import Optional

from fastapi import Security, Request
from fastapi.security import APIKeyHeader

from backend.core.config import get_settings
from backend.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    request: Request,
    api_key: Optional[str] = Security(_api_key_header),
) -> Optional[str]:
    """
    FastAPI dependency that validates the ``X-API-Key`` header.

    If ``API_KEY`` is not configured (empty), authentication is skipped
    so local development works without extra headers.

    Returns:
        The validated API key string, or None if auth is disabled.

    Raises:
        AuthenticationError: If the key is missing or invalid.
    """
    settings = get_settings()

    # Auth disabled when no key is configured
    if not settings.api_key:
        return None

    if not api_key:
        logger.warning("Missing API key from %s", request.client.host if request.client else "unknown")
        raise AuthenticationError("Missing API key. Provide it via the X-API-Key header.")

    if api_key != settings.api_key:
        logger.warning("Invalid API key attempt from %s", request.client.host if request.client else "unknown")
        raise AuthenticationError("Invalid API key.")

    return api_key
