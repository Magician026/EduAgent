"""Centralized runtime configuration for EduAgent."""

from __future__ import annotations

import os
from collections.abc import Mapping
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


@dataclass(frozen=True)
class Settings:
    """Validated application settings with paths scoped to the project runtime."""

    data_dir: Path
    runtime_dir: Path
    database_path: Path
    chroma_path: Path
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str
    embedding_model: str
    retrieval_top_k: int = 5
    student_id: str = "demo_student"

    @property
    def llm_configured(self) -> bool:
        """Return whether chat generation has enough configuration to run."""

        return bool(self.openai_api_key and self.openai_model)

    @property
    def embeddings_configured(self) -> bool:
        """Return whether embedding generation has enough configuration to run."""

        return bool(self.openai_api_key and self.embedding_model)

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

        return cls(
            data_dir=data_dir,
            runtime_dir=runtime_dir,
            database_path=runtime_dir / "eduagent.db",
            chroma_path=runtime_dir / "chroma",
            openai_api_key=_source_value("OPENAI_API_KEY", values, secrets),
            openai_base_url=_source_value("OPENAI_BASE_URL", values, secrets),
            openai_model=(
                _source_value("OPENAI_MODEL", values, secrets, "gpt-4o-mini") or "gpt-4o-mini"
            ),
            embedding_model=(
                _source_value(
                    "OPENAI_EMBEDDING_MODEL", values, secrets, "text-embedding-3-small"
                )
                or "text-embedding-3-small"
            ),
            retrieval_top_k=retrieval_top_k,
        )
