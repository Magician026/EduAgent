"""Deterministic page-preserving text chunking."""

from __future__ import annotations

from collections.abc import Sequence

from eduagent.models import DocumentChunk, PageText


def chunk_pages(
    pages: Sequence[PageText],
    max_chars: int = 1000,
    overlap: int = 150,
) -> list[DocumentChunk]:
    """Split each page independently into overlapping character chunks."""

    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be non-negative and smaller than max_chars")

    chunks: list[DocumentChunk] = []
    for page in pages:
        start = 0
        ordinal = 0
        while start < len(page.text):
            end = min(start + max_chars, len(page.text))
            text = page.text[start:end].strip()
            if text:
                chunks.append(
                    DocumentChunk(
                        document_name=page.document_name,
                        document_hash=page.document_hash,
                        page=page.page,
                        chunk_id=f"{page.document_hash[:12]}-{page.page}-{ordinal}",
                        text=text,
                    )
                )
            if end == len(page.text):
                break
            start = end - overlap
            ordinal += 1
    return chunks
