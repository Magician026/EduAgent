"""Orchestration for hashing, parsing, embedding, and storing course files."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from typing import Protocol

from eduagent.document_processing.chunker import chunk_pages
from eduagent.document_processing.parser import parse_pdf
from eduagent.models import DocumentChunk, IngestionResult


class EmbeddingService(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorStorage(Protocol):
    def add(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None: ...


class DocumentRepository(Protocol):
    def document_exists(self, document_hash: str) -> bool: ...

    def register_document(
        self,
        document_name: str,
        document_hash: str,
        page_count: int,
        chunk_count: int,
    ) -> None: ...


class IngestionService:
    """Coordinate document ingestion without depending on Streamlit."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStorage,
        repository: DocumentRepository,
        embedding_batch_size: int = 32,
    ) -> None:
        if embedding_batch_size < 1:
            raise ValueError("embedding_batch_size must be at least 1")
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.repository = repository
        self.embedding_batch_size = embedding_batch_size

    def ingest(
        self,
        file_name: str,
        pdf_bytes: bytes,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> IngestionResult:
        """Index a PDF or return a duplicate result for previously indexed content."""

        document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        if self.repository.document_exists(document_hash):
            return IngestionResult(
                status="duplicate",
                document_hash=document_hash,
                page_count=0,
                chunk_count=0,
                message=f"{file_name} is already indexed.",
            )

        pages = parse_pdf(file_name, pdf_bytes)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("The PDF produced no usable chunks.")
        embeddings: list[list[float]] = []
        for start in range(0, len(chunks), self.embedding_batch_size):
            batch = chunks[start : start + self.embedding_batch_size]
            batch_embeddings = self.embedding_service.embed([chunk.text for chunk in batch])
            if len(batch_embeddings) != len(batch):
                raise ValueError("The embedding provider returned an unexpected vector count.")
            embeddings.extend(batch_embeddings)
            if progress_callback is not None:
                progress_callback(min(start + len(batch), len(chunks)), len(chunks))
        self.vector_store.add(chunks, embeddings)
        self.repository.register_document(
            file_name,
            document_hash,
            page_count=len(pages),
            chunk_count=len(chunks),
        )
        return IngestionResult(
            status="indexed",
            document_hash=document_hash,
            page_count=len(pages),
            chunk_count=len(chunks),
            message=f"Indexed {file_name}: {len(pages)} page(s), {len(chunks)} chunk(s).",
        )
