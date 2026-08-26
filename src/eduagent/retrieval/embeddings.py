"""Embedding provider contracts and adapters."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from openai import OpenAI

from eduagent.llm.provider import ProviderConfigurationError, ProviderRequestError


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbeddingProvider:
    """Embedding adapter with credentials independent from the chat provider."""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ProviderConfigurationError("Embedding API key is not configured.")
        if not model:
            raise ProviderConfigurationError("Embedding model is not configured.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key, base_url=base_url or None)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Create embeddings for a non-empty sequence of texts."""

        if not texts:
            raise ValueError("At least one text is required for embedding.")
        try:
            response = self.client.embeddings.create(model=self.model, input=list(texts))
            vectors = [list(item.embedding) for item in response.data]
        except Exception as exc:
            raise ProviderRequestError("The embedding request failed. Please retry.") from exc
        if len(vectors) != len(texts):
            raise ProviderRequestError(
                "The embedding provider returned an unexpected vector count."
            )
        return vectors


class OpenAIEmbeddingProvider:
    """Backward-compatible wrapper around an existing embedding-capable provider."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self.provider.embed(texts)
