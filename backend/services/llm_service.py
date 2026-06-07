"""
KnowledgeHive - LLM Service

Abstracted LLM provider with OpenRouter implementation.
Protocol-based design allows swapping providers (Azure OpenAI, OpenAI, etc.)

Phase 3: Added optional CacheManager integration for caching LLM responses.
"""

import json
import logging
from typing import Protocol, Optional, TYPE_CHECKING

import httpx

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# --- Configure Langfuse Context (Optional) ---
try:
    from langfuse.decorators import langfuse_context
    settings = get_settings()
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse_context.configure(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        logger.info("Langfuse tracing enabled and configured.")
    else:
        logger.info("Langfuse keys not found. Tracing disabled.")
except ImportError:
    logger.warning("Langfuse package not installed. Tracing disabled.")
except Exception as e:
    logger.warning(f"Failed to configure Langfuse: {e}")

if TYPE_CHECKING:
    from backend.services.cache import CacheManager


class LLMProvider(Protocol):
    """Protocol for LLM providers. Implement this to add new providers."""

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response from the LLM."""
        ...


class OpenRouterProvider:
    """LLM provider using OpenRouter API, with optional Redis caching."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        cache_manager: Optional["CacheManager"] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._cache = cache_manager

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://knowledgehive.app",
                    "X-Title": "KnowledgeHive",
                },
            )
        return self._client

    # If Langfuse is available, wrap with observe
    try:
        from langfuse.decorators import observe
        _generate_decorator = observe(as_type="generation")
    except ImportError:
        def _generate_decorator(func):
            return func

    @_generate_decorator
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a response via OpenRouter API.

        If a CacheManager is configured, identical prompts will return
        cached responses instead of making an API call (saves cost + time).
        Caching is skipped for non-deterministic calls (temperature > 0.5).
        """
        use_cache = self._cache is not None and temperature <= 0.5

        # --- Check cache ---
        cache_key = None
        if use_cache:
            cache_key = self._cache.make_llm_key(prompt, system_prompt, self.model)
            try:
                cached = await self._cache.get_cached_llm_response(cache_key)
                if cached is not None:
                    logger.info("LLM cache HIT — returning cached response")
                    return cached
            except Exception as e:
                logger.warning(f"Cache read failed (proceeding without cache): {e}")

        # --- Call OpenRouter API ---
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            # --- Store in cache ---
            if use_cache and cache_key:
                try:
                    await self._cache.cache_llm_response(cache_key, result)
                    logger.info("LLM cache MISS — response cached for next time")
                except Exception as e:
                    logger.warning(f"Cache write failed (non-critical): {e}")

            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"LLM API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Future providers can be added here:
# class AzureOpenAIProvider: ...
# class OpenAIProvider: ...
