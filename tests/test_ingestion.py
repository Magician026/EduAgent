from dataclasses import dataclass

from eduagent.document_processing.ingestion import IngestionService


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
