from dataclasses import dataclass

from eduagent import document_processing
from eduagent.document_processing.ingestion import IngestionService
from eduagent.models import DocumentChunk, PageText


@dataclass
class FakeEmbeddings:
    calls: int = 0

    def embed(self, texts):
        self.calls += 1
        return [[float(len(text)), 1.0] for text in texts]


@dataclass
class FakeVectorStore:
    added_chunks: list = None

    def __post_init__(self):
        self.added_chunks = []

    def add(self, chunks, embeddings):
        self.added_chunks.extend(chunks)


class FakeRepository:
    def __init__(self):
        self.hashes = set()
        self.documents = []

    def document_exists(self, document_hash):
        return document_hash in self.hashes

    def register_document(self, document_name, document_hash, page_count, chunk_count):
        self.hashes.add(document_hash)
        self.documents.append((document_name, page_count, chunk_count))


def test_ingestion_indexes_document_and_preserves_chunks(sample_pdf_bytes):
    embeddings = FakeEmbeddings()
    vector_store = FakeVectorStore()
    repository = FakeRepository()
    service = IngestionService(embeddings, vector_store, repository)

    result = service.ingest("lesson.pdf", sample_pdf_bytes)

    assert result.status == "indexed"
    assert result.page_count == 1
    assert result.chunk_count >= 1
    assert embeddings.calls == 1
    assert vector_store.added_chunks[0].document_name == "lesson.pdf"
    assert repository.documents[0][0] == "lesson.pdf"


def test_ingestion_skips_duplicate_content(sample_pdf_bytes):
    embeddings = FakeEmbeddings()
    vector_store = FakeVectorStore()
    repository = FakeRepository()
    service = IngestionService(embeddings, vector_store, repository)

    first = service.ingest("lesson.pdf", sample_pdf_bytes)
    second = service.ingest("renamed-lesson.pdf", sample_pdf_bytes)

    assert first.status == "indexed"
    assert second.status == "duplicate"
    assert embeddings.calls == 1
    assert len(repository.documents) == 1


def test_ingestion_batches_embeddings_and_reports_progress(monkeypatch):
    pages = [
        PageText(
            document_name="lesson.pdf",
            document_hash="hash",
            page=1,
            text="lesson",
        )
    ]
    chunks = [
        DocumentChunk(
            document_name="lesson.pdf",
            document_hash="hash",
            page=1,
            chunk_id=f"chunk-{index}",
            text=f"chunk {index}",
        )
        for index in range(5)
    ]

    monkeypatch.setattr(document_processing.ingestion, "parse_pdf", lambda *_: pages)
    monkeypatch.setattr(document_processing.ingestion, "chunk_pages", lambda *_: chunks)

    class RecordingEmbeddings:
        def __init__(self):
            self.calls = []

        def embed(self, texts):
            self.calls.append(list(texts))
            return [[1.0, 0.0] for _ in texts]

    embeddings = RecordingEmbeddings()
    vector_store = FakeVectorStore()
    repository = FakeRepository()
    service = IngestionService(
        embeddings,
        vector_store,
        repository,
        embedding_batch_size=2,
    )
    progress = []

    result = service.ingest(
        "lesson.pdf",
        b"pdf",
        progress_callback=lambda completed, total: progress.append((completed, total)),
    )

    assert result.status == "indexed"
    assert [len(call) for call in embeddings.calls] == [2, 2, 1]
    assert progress == [(2, 5), (4, 5), (5, 5)]
