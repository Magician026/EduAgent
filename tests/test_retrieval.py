import pytest

from eduagent.llm.provider import OpenAICompatibleProvider, ProviderConfigurationError
from eduagent.models import DocumentChunk, RetrievedChunk
from eduagent.retrieval.retriever import Retriever
from eduagent.retrieval.vector_store import ChromaVectorStore


class FakeEmbeddings:
    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


class FakeVectorStore:
    def __init__(self):
        self.results = [
            RetrievedChunk(
                chunk=DocumentChunk(
                    document_name="lecture_05.pdf",
                    document_hash="hash",
                    page=12,
                    chunk_id="chunk-1",
                    text="MAP classification chooses the most probable class.",
                ),
                similarity=0.91,
            )
        ]

    def search(self, query_embedding, k):
        return self.results[:k]


def test_retriever_returns_metadata_and_excerpt():
    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeVectorStore(),
        top_k=3,
    )

    results = retriever.retrieve("What is MAP classification?")

    assert results[0].chunk.page == 12
    assert "lecture_05.pdf — Page 12" in retriever.format_context(results)


def test_chroma_vector_store_returns_metadata(tmp_path):
    store = ChromaVectorStore(tmp_path / "chroma", collection_name="test_collection")
    chunk = DocumentChunk(
        document_name="lecture_05.pdf",
        document_hash="hash",
        page=12,
        chunk_id="chunk-1",
        text="MAP classification chooses the most probable class.",
    )

    store.add([chunk], [[1.0, 0.0]])
    results = store.search([1.0, 0.0], k=1)

    assert len(results) == 1
    assert results[0].chunk.document_name == "lecture_05.pdf"
    assert results[0].chunk.page == 12
    assert results[0].chunk.text.startswith("MAP classification")


def test_missing_key_raises_safe_provider_error():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAICompatibleProvider(api_key=None, model="model", embedding_model="embed")
