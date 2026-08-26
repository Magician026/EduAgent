"""Deterministic detection for document-level overview questions."""

from __future__ import annotations

OVERVIEW_PHRASES = (
    "介绍一下",
    "讲了什么",
    "主要内容",
    "整体内容",
    "全文概述",
    "文档概述",
    "pdf overview",
    "document overview",
    "what is this pdf about",
    "what does this document cover",
    "summarize this document",
)


def is_document_overview_query(query: str) -> bool:
    """Return whether ``query`` asks for a broad document overview."""

    normalized_query = query.strip().casefold()
    return bool(normalized_query) and any(
        phrase in normalized_query for phrase in OVERVIEW_PHRASES
    )
