"""
KnowledgeHive - Rate Limiter

Provides a global slowapi Limiter instance.

Phase 3: Uses Redis as storage backend so rate limits persist across
restarts and work across multiple backend instances.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import get_settings


def _build_storage_uri() -> str:
    """Build a Redis URI for slowapi storage, with fallback to memory."""
    if os.environ.get("TESTING") == "1":
        return "memory://"
        
    try:
        settings = get_settings()
        host = settings.redis_host
        port = settings.redis_port
        password = settings.redis_password
        if password:
            return f"redis://:{password}@{host}:{port}/2"
        return f"redis://{host}:{port}/2"
    except Exception:
        # Fallback to in-memory if config isn't available yet
        return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_build_storage_uri(),
)
