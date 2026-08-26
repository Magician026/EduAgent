from eduagent.config import Settings


def test_settings_read_provider_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    settings = Settings.from_sources()

    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "test-model"
    assert settings.llm_configured is True


def test_settings_reports_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = Settings.from_sources()

    assert settings.llm_configured is False


def test_settings_supports_separate_llm_and_embedding_providers():
    settings = Settings.from_sources(
        env={
            "EDUAGENT_LLM_API_KEY": "deepseek-key",
            "EDUAGENT_LLM_BASE_URL": "https://api.deepseek.com",
            "EDUAGENT_LLM_MODEL": "deepseek-v4-flash",
            "EDUAGENT_EMBEDDING_API_KEY": "openai-key",
            "EDUAGENT_EMBEDDING_BASE_URL": "https://api.openai.com/v1",
            "EDUAGENT_EMBEDDING_MODEL": "text-embedding-3-small",
        }
    )

    assert settings.llm_api_key == "deepseek-key"
    assert settings.llm_base_url == "https://api.deepseek.com"
    assert settings.llm_model == "deepseek-v4-flash"
    assert settings.embedding_api_key == "openai-key"
    assert settings.embedding_base_url == "https://api.openai.com/v1"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.llm_configured is True
    assert settings.embeddings_configured is True


def test_provider_neutral_llm_does_not_fake_embedding_readiness():
    settings = Settings.from_sources(
        env={
            "EDUAGENT_LLM_API_KEY": "deepseek-key",
            "EDUAGENT_LLM_BASE_URL": "https://api.deepseek.com",
            "EDUAGENT_LLM_MODEL": "deepseek-v4-flash",
        }
    )

    assert settings.llm_configured is True
    assert settings.embeddings_configured is False


def test_legacy_openai_settings_still_configure_both_clients():
    settings = Settings.from_sources(
        env={
            "OPENAI_API_KEY": "legacy-key",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "legacy-chat",
            "OPENAI_EMBEDDING_MODEL": "legacy-embedding",
        }
    )

    assert settings.llm_api_key == "legacy-key"
    assert settings.embedding_api_key == "legacy-key"
    assert settings.embedding_base_url == "https://api.openai.com/v1"
    assert settings.openai_api_key == "legacy-key"
    assert settings.openai_model == "legacy-chat"
