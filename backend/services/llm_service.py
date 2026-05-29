"""
KnowledgeHive - LLM Service

Abstracted LLM provider with OpenRouter implementation.
Protocol-based design allows swapping providers (Azure OpenAI, OpenAI, etc.)
"""

import json
import logging
from typing import Protocol, Optional

import httpx

logger = logging.getLogger(__name__)


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
    """LLM provider using OpenRouter API."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

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

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response via OpenRouter API."""
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
            return data["choices"][0]["message"]["content"]
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
