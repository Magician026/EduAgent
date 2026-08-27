import pytest

from eduagent.llm.provider import OpenAICompatibleProvider, ProviderConfigurationError
from eduagent.models import DocumentChunk, RetrievedChunk
from eduagent.retrieval.embeddings import OpenAICompatibleEmbeddingProvider
from eduagent.retrieval.query_intent import is_document_overview_query
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


@pytest.mark.parametrize(
    "query",
    [
        "帮我介绍一下这个pdf讲了什么内容",
        "帮我总结一下这个 PDF",
        "Summarize this PDF",
        "Give me an overview of this document",
        "What is this document about?",
        "帮我总结一下这本书有哪些章节",
        "这本书主要讲了什么",
        "What is this book about?",
        "What chapters does this book contain?",
        "这本书分为哪些章节？",
        "List the chapters in this book.",
    ],
)
def test_document_overview_intent_detects_broad_document_questions(query):
    assert is_document_overview_query(query) is True


@pytest.mark.parametrize(
    "query",
    [
        "什么是 XGBoost？",
        "介绍一下 XGBoost",
        "第三章讲了什么？",
        "Summarize XGBoost",
        "What does chapter 3 cover?",
        "介绍一下本文中的 XGBoost",
        "总结一下这篇文章的实验部分",
        "Summarize this document's section on XGBoost",
        "总结一下本书的实验部分",
        "Summarize this book's section on XGBoost",
        "总结一下这本书关于 XGBoost 的内容",
        "Summarize XGBoost in this book.",
        "Summarize section 2 of this book.",
    ],
)
def test_document_overview_intent_keeps_focused_questions_on_normal_path(query):
    assert is_document_overview_query(query) is False


def test_document_overview_retrieval_spreads_evidence_across_document():
    def chunk(page, text):
        return DocumentChunk(
            document_name="book.pdf",
            document_hash="hash",
            page=page,
            chunk_id=f"chunk-{page}",
            text=text,
        )

    class FakeOverviewVectorStore:
        def __init__(self, chunks):
            self.chunks = chunks

        def all_chunks(self):
            return self.chunks

    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeOverviewVectorStore(
            chunks=[
                chunk(page=1, text="Book title and author"),
                chunk(page=10, text="Contents 1 Introduction 5 Analytic Learning 89"),
                chunk(page=19, text="Chapter 1 Introduction Pattern Recognition"),
                chunk(page=89, text="Chapter 5 Analytic Learning"),
                chunk(page=161, text="Chapter 6 Penalized Learning"),
                chunk(page=266, text="Chapter 9 Ensemble Learning"),
                chunk(page=400, text="Appendix references"),
            ]
        ),
    )
    results = retriever.retrieve_document_overview()

    pages = {result.chunk.page for result in results}
    assert {10, 19, 89, 161, 266}.issubset(pages)


def test_document_overview_retrieval_fills_the_per_document_cap():
    class FakeOverviewVectorStore:
        def all_chunks(self):
            return [
                DocumentChunk(
                    document_name="book.pdf",
                    document_hash="hash",
                    page=page,
                    chunk_id=f"chunk-{page}",
                    text="Chapter summary" if page <= 10 else f"Page {page}",
                )
                for page in range(1, 41)
            ]

    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeOverviewVectorStore(),
    )

    results = retriever.retrieve_document_overview()

    assert len(results) == 32


def test_document_overview_retrieval_ignores_chapter_mentions_in_body_text():
    class FakeOverviewVectorStore:
        def all_chunks(self):
            return [
                DocumentChunk(
                    document_name="book.pdf",
                    document_hash="hash",
                    page=page,
                    chunk_id=f"chunk-{page}",
                    text="This chapter explains a concept in the book.",
                )
                for page in range(1, 101)
            ]

    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeOverviewVectorStore(),
    )

    results = retriever.retrieve_document_overview()

    assert max(result.chunk.page for result in results) == 100


def test_document_overview_retrieval_reserves_late_pages_when_structure_saturates():
    class FakeOverviewVectorStore:
        def all_chunks(self):
            return [
                DocumentChunk(
                    document_name="book.pdf",
                    document_hash="hash",
                    page=page,
                    chunk_id=f"chunk-{page}",
                    text=f"Contents Chapter {page}",
                )
                for page in range(1, 101)
            ]

    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeOverviewVectorStore(),
    )

    results = retriever.retrieve_document_overview()

    pages = {result.chunk.page for result in results}
    assert 100 in pages
    assert any(page > 75 for page in pages)


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


def test_chroma_vector_store_all_chunks_reconstructs_metadata_and_text(tmp_path):
    store = ChromaVectorStore(tmp_path / "chroma", collection_name="all_chunks_collection")
    chunks = [
        DocumentChunk(
            document_name="book.pdf",
            document_hash="hash",
            page=2,
            chunk_id="chunk-2",
            text="Second page excerpt.",
        ),
        DocumentChunk(
            document_name="book.pdf",
            document_hash="hash",
            page=11,
            chunk_id="chunk-11",
            text="Eleventh page excerpt.",
        ),
    ]

    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])

    reconstructed = {chunk.chunk_id: chunk for chunk in store.all_chunks()}

    assert reconstructed == {chunk.chunk_id: chunk for chunk in chunks}


def test_missing_key_raises_safe_provider_error():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAICompatibleProvider(api_key=None, model="model")


def test_embedding_provider_uses_its_own_model_and_client():
    class FakeEmbeddingClient:
        class embeddings:
            @staticmethod
            def create(**kwargs):
                assert kwargs == {"model": "text-embedding-3-small", "input": ["hello"]}
                return type(
                    "Response",
                    (),
                    {"data": [type("Item", (), {"embedding": [0.1, 0.2]})()]},
                )()

    provider = OpenAICompatibleEmbeddingProvider(
        api_key="embedding-key",
        base_url="https://api.openai.com/v1",
        model="text-embedding-3-small",
        client=FakeEmbeddingClient(),
    )

    assert provider.embed(["hello"]) == [[0.1, 0.2]]


def test_missing_embedding_key_raises_safe_provider_error():
    with pytest.raises(ProviderConfigurationError, match="Embedding API key"):
        OpenAICompatibleEmbeddingProvider(
            api_key=None,
            model="text-embedding-3-small",
        )
