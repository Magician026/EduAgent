"""Query retrieval and grounded-context formatting."""

from __future__ import annotations

import re
from collections.abc import Sequence

from eduagent.models import DocumentChunk, RetrievedChunk
from eduagent.retrieval.embeddings import EmbeddingProvider

CONTENTS_SIGNALS = ("contents", "table of contents", "目录", "目次")
CHAPTER_HEADING_PATTERN = re.compile(
    r"^(?:chapter\s+(?:\d+|[ivxlcdm]+)\b|章节\s*[一二三四五六七八九十百千\d]+|第\s*[一二三四五六七八九十百千\d]+\s*章)",
    re.IGNORECASE,
)
SUMMARY_HEADING_PATTERN = re.compile(
    r"^(?:chapter\s+summary|summary|本章小结|小结|总结)(?:\s|$|[:：])",
    re.IGNORECASE,
)
OVERVIEW_CHUNK_LIMIT = 32
OVERVIEW_STRUCTURAL_CHUNK_LIMIT = OVERVIEW_CHUNK_LIMIT // 2


class Retriever:
    """Embed a query, search the vector store, and format citations for prompts."""

    def __init__(self, embedding_provider: EmbeddingProvider, vector_store, top_k: int = 5) -> None:
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        query_embedding = self.embedding_provider.embed([query])[0]
        return self.vector_store.search(query_embedding, k or self.top_k)

    def retrieve_document_overview(self) -> list[RetrievedChunk]:
        """Select structural and distributed evidence for every indexed document."""

        chunks_by_document: dict[str, list[DocumentChunk]] = {}
        for chunk in self.vector_store.all_chunks():
            chunks_by_document.setdefault(chunk.document_hash, []).append(chunk)

        results: list[RetrievedChunk] = []
        for chunks in chunks_by_document.values():
            selected = self._select_overview_chunks(chunks)
            results.extend(RetrievedChunk(chunk=chunk, similarity=0.0) for chunk in selected)
        return results

    @staticmethod
    def _select_overview_chunks(chunks: Sequence[DocumentChunk]) -> list[DocumentChunk]:
        ordered_chunks = sorted(chunks, key=lambda chunk: (chunk.page, chunk.chunk_id))
        selected: list[DocumentChunk] = []
        selected_ids: set[str] = set()

        def add_matching(matches) -> None:
            for chunk in ordered_chunks:
                if len(selected) == OVERVIEW_STRUCTURAL_CHUNK_LIMIT:
                    return
                if chunk.chunk_id not in selected_ids and matches(chunk.text):
                    selected.append(chunk)
                    selected_ids.add(chunk.chunk_id)

        add_matching(lambda text: any(signal in text.casefold() for signal in CONTENTS_SIGNALS))
        add_matching(
            lambda text: bool(
                CHAPTER_HEADING_PATTERN.match(text.lstrip())
                or SUMMARY_HEADING_PATTERN.match(text.lstrip())
            )
        )

        remaining_chunks = [
            chunk for chunk in ordered_chunks if chunk.chunk_id not in selected_ids
        ]
        remaining = min(OVERVIEW_CHUNK_LIMIT - len(selected), len(remaining_chunks))
        for index in range(remaining):
            chunk = remaining_chunks[
                index * (len(remaining_chunks) - 1) // max(remaining - 1, 1)
            ]
            selected.append(chunk)
        return selected

    @staticmethod
    def format_context(results: Sequence[RetrievedChunk]) -> str:
        """Format retrieved excerpts with source labels for a grounded prompt."""

        if not results:
            return "No relevant course material was retrieved."
        blocks = []
        for result in results:
            chunk = result.chunk
            blocks.append(
                "\n".join(
                    [
                        f"Source: {chunk.document_name} — Page {chunk.page}",
                        f"Chunk ID: {chunk.chunk_id}",
                        chunk.text,
                    ]
                )
            )
        return "\n\n---\n\n".join(blocks)
