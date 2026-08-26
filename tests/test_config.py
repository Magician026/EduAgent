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
