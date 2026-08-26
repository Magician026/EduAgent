"""Query retrieval and grounded-context formatting."""

from __future__ import annotations

from collections.abc import Sequence

from eduagent.models import RetrievedChunk
from eduagent.retrieval.embeddings import EmbeddingProvider


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
