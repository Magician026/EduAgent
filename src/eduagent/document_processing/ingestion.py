"""Orchestration for hashing, parsing, embedding, and storing course files."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
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
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.repository = repository

    def ingest(self, file_name: str, pdf_bytes: bytes) -> IngestionResult:
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
        embeddings = self.embedding_service.embed([chunk.text for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise ValueError("The embedding provider returned an unexpected vector count.")
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
