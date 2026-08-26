from eduagent.config import Settings
from eduagent.ui.services import build_services


def test_build_services_wires_llm_and_embedding_providers_independently(
    tmp_path, monkeypatch
):
    calls = {}

    class FakeLLMProvider:
        def __init__(self, **kwargs):
            calls["llm"] = kwargs

    class FakeEmbeddingProvider:
        def __init__(self, **kwargs):
            calls["embedding"] = kwargs

    monkeypatch.setattr("eduagent.ui.services.OpenAICompatibleProvider", FakeLLMProvider)
    monkeypatch.setattr(
        "eduagent.ui.services.OpenAICompatibleEmbeddingProvider", FakeEmbeddingProvider
    )
    settings = Settings.from_sources(
        env={
            "EDUAGENT_DATA_DIR": str(tmp_path / "data"),
            "EDUAGENT_LLM_API_KEY": "deepseek-key",
            "EDUAGENT_LLM_BASE_URL": "https://api.deepseek.com",
            "EDUAGENT_LLM_MODEL": "deepseek-v4-flash",
            "EDUAGENT_EMBEDDING_API_KEY": "openai-key",
            "EDUAGENT_EMBEDDING_BASE_URL": "https://api.openai.com/v1",
            "EDUAGENT_EMBEDDING_MODEL": "text-embedding-3-small",
        }
    )

    services = build_services(settings)

    assert calls["llm"] == {
        "api_key": "deepseek-key",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    }
    assert calls["embedding"] == {
        "api_key": "openai-key",
        "base_url": "https://api.openai.com/v1",
        "model": "text-embedding-3-small",
    }
    assert services.tutor is not None
    assert services.ingestion is not None
