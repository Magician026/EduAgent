"""Centralized runtime configuration for EduAgent."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _source_value(
    key: str,
    env: Mapping[str, str],
    secrets: Mapping[str, Any] | None,
    default: str | None = None,
) -> str | None:
    """Read a setting from environment first, then an optional secrets mapping."""

    value = env.get(key)
    if value is not None and value != "":
        return value
    if secrets is not None:
        secret_value = secrets.get(key)
        if secret_value is not None and str(secret_value) != "":
            return str(secret_value)
    return default


def _first_source_value(
    keys: Sequence[str],
    env: Mapping[str, str],
    secrets: Mapping[str, Any] | None,
    default: str | None = None,
) -> str | None:
    """Read the first configured value from a list of aliases."""

    for key in keys:
        value = _source_value(key, env, secrets)
        if value is not None:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    """Validated application settings with paths scoped to the project runtime."""

    data_dir: Path
    runtime_dir: Path
    database_path: Path
    chroma_path: Path
    llm_api_key: str | None
    llm_base_url: str | None
    llm_model: str
    embedding_api_key: str | None
    embedding_base_url: str | None
    embedding_model: str
    retrieval_top_k: int = 5
    student_id: str = "demo_student"

    @property
    def llm_configured(self) -> bool:
        """Return whether chat generation has enough configuration to run."""

        return bool(self.llm_api_key and self.llm_model)

    @property
    def embeddings_configured(self) -> bool:
        """Return whether embedding generation has enough configuration to run."""

        return bool(self.embedding_api_key and self.embedding_model)

    @property
    def openai_api_key(self) -> str | None:
        """Backward-compatible alias for the LLM API key."""

        return self.llm_api_key

    @property
    def openai_base_url(self) -> str | None:
        """Backward-compatible alias for the LLM base URL."""

        return self.llm_base_url

    @property
    def openai_model(self) -> str:
        """Backward-compatible alias for the LLM model."""

        return self.llm_model

    def ensure_runtime_directories(self) -> None:
        """Create local runtime directories when the application starts."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_sources(
        cls,
        env: Mapping[str, str] | None = None,
        secrets: Mapping[str, Any] | None = None,
    ) -> Settings:
        """Build settings from environment variables and optional Streamlit secrets."""

        load_dotenv(override=False)
        values = os.environ if env is None else env
        data_dir = Path(_source_value("EDUAGENT_DATA_DIR", values, secrets, "data"))
        runtime_dir = data_dir / "runtime"
        top_k_value = _source_value("EDUAGENT_RETRIEVAL_TOP_K", values, secrets, "5")
        try:
            retrieval_top_k = int(top_k_value or "5")
        except ValueError as exc:
            raise ValueError("EDUAGENT_RETRIEVAL_TOP_K must be an integer") from exc
        if retrieval_top_k < 1:
            raise ValueError("EDUAGENT_RETRIEVAL_TOP_K must be at least 1")

        llm_api_key = _first_source_value(
            ("EDUAGENT_LLM_API_KEY", "OPENAI_API_KEY"), values, secrets
        )
        llm_base_url = _first_source_value(
            ("EDUAGENT_LLM_BASE_URL", "OPENAI_BASE_URL"), values, secrets
        )
        llm_model = (
            _first_source_value(
                ("EDUAGENT_LLM_MODEL", "OPENAI_MODEL"), values, secrets, "gpt-4o-mini"
            )
            or "gpt-4o-mini"
        )
        embedding_api_key = _first_source_value(
            ("EDUAGENT_EMBEDDING_API_KEY", "OPENAI_EMBEDDING_API_KEY"), values, secrets
        )
        embedding_base_url = _first_source_value(
            ("EDUAGENT_EMBEDDING_BASE_URL", "OPENAI_EMBEDDING_BASE_URL"), values, secrets
        )
        embedding_model = (
            _first_source_value(
                ("EDUAGENT_EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL"),
                values,
                secrets,
                "text-embedding-3-small",
            )
            or "text-embedding-3-small"
        )
        has_provider_neutral_llm = any(
            _source_value(key, values, secrets) is not None
            for key in ("EDUAGENT_LLM_API_KEY", "EDUAGENT_LLM_BASE_URL", "EDUAGENT_LLM_MODEL")
        )
        if not has_provider_neutral_llm:
            embedding_api_key = embedding_api_key or llm_api_key
            embedding_base_url = embedding_base_url or llm_base_url

        return cls(
            data_dir=data_dir,
            runtime_dir=runtime_dir,
            database_path=runtime_dir / "eduagent.db",
            chroma_path=runtime_dir / "chroma",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            embedding_api_key=embedding_api_key,
            embedding_base_url=embedding_base_url,
            embedding_model=embedding_model,
            retrieval_top_k=retrieval_top_k,
        )
