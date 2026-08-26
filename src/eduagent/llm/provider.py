"""OpenAI-compatible provider with safe errors and structured output validation."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMProvider(Protocol):
    def complete_text(self, system: str, user: str, *, temperature: float = 0.2) -> str: ...

    def complete_json(
        self,
        model_type: type[ModelT],
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
    ) -> ModelT: ...


class ProviderError(RuntimeError):
    """Base class for user-safe provider failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when required provider configuration is missing."""


class ProviderRequestError(ProviderError):
    """Raised when a remote provider request fails or returns no content."""


class StructuredOutputError(ProviderError):
    """Raised when structured output remains invalid after one repair attempt."""


class OpenAICompatibleProvider:
    """Synchronous provider adapter for OpenAI-compatible chat APIs."""

    def __init__(
        self,
        api_key: str | None,
        model: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured.")
        if not model:
            raise ProviderConfigurationError("OPENAI_MODEL is not configured.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key, base_url=base_url or None)

    def _chat(self, system: str, user: str, *, temperature: float, json_mode: bool = False) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise ProviderRequestError("The model request failed. Please retry.") from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ProviderRequestError("The model returned an empty response.") from exc
        if not content or not str(content).strip():
            raise ProviderRequestError("The model returned an empty response.")
        return str(content).strip()

    def complete_text(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        """Return a plain-text chat completion."""

        return self._chat(system, user, temperature=temperature)

    def complete_json(
        self,
        model_type: type[ModelT],
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
    ) -> ModelT:
        """Generate and validate one structured object, with one repair attempt."""

        raw = self._chat(system, user, temperature=temperature, json_mode=True)
        try:
            return model_type.model_validate_json(raw)
        except ValidationError as first_error:
            repair_system = (
                "Return only one valid JSON object matching the requested schema. "
                "Do not add Markdown fences or explanatory text."
            )
            repair_user = f"Repair this invalid JSON output so it matches the schema:\n{raw}"
            try:
                repaired = self._chat(repair_system, repair_user, temperature=0.0, json_mode=True)
                return model_type.model_validate_json(repaired)
            except (ValidationError, ProviderError) as repair_error:
                raise StructuredOutputError(
                    f"The provider returned invalid structured output for {model_type.__name__}."
                ) from repair_error
            except Exception as repair_error:
                raise StructuredOutputError(
                    f"The provider returned invalid structured output for {model_type.__name__}."
                ) from repair_error
            finally:
                del first_error
