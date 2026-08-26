"""Persistent local Chroma vector storage."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import chromadb

from eduagent.models import DocumentChunk, RetrievedChunk


class ChromaVectorStore:
    """Store and search page-aware chunks in a local Chroma collection."""

    def __init__(self, path: Path, collection_name: str = "eduagent_course") -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self.collection.count()

    def add(
        self,
        chunks: Sequence[DocumentChunk],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """Add chunks and their provider-generated vectors."""

        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts must match.")
        if not chunks:
            return
        self.collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=[list(vector) for vector in embeddings],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "document_name": chunk.document_name,
                    "document_hash": chunk.document_hash,
                    "page": chunk.page,
                    "chunk_id": chunk.chunk_id,
                }
                for chunk in chunks
            ],
        )

    def search(self, query_embedding: Sequence[float], k: int) -> list[RetrievedChunk]:
        """Return up to ``k`` chunks with cosine similarity scores."""

        if k < 1 or self.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        matches: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
            if not metadata:
                continue
            similarity = max(-1.0, min(1.0, 1.0 - float(distance)))
            chunk = DocumentChunk(
                document_name=str(metadata["document_name"]),
                document_hash=str(metadata["document_hash"]),
                page=int(metadata["page"]),
                chunk_id=str(metadata["chunk_id"]),
                text=str(document),
            )
            matches.append(RetrievedChunk(chunk=chunk, similarity=similarity))
        return matches
