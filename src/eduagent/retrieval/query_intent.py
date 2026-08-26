"""Deterministic detection for document-level overview questions."""

from __future__ import annotations

import re

DOCUMENT_REFERENCES = (
    "pdf",
    "document",
    "this file",
    "the file",
    "这个文档",
    "这份文档",
    "这篇文章",
    "本文",
)
OVERVIEW_REQUESTS = (
    "介绍一下",
    "讲了什么",
    "主要内容",
    "整体内容",
    "全文概述",
    "文档概述",
    "总结一下",
    "总结",
    "概述",
    "summary",
    "summarize",
    "overview",
    "what is this pdf about",
    "what is this document about",
    "what does this document cover",
)
IMPLICIT_DOCUMENT_OVERVIEWS = ("全文概述", "文档概述")
FOCUSED_CHAPTER_PATTERN = re.compile(
    r"(?:第\s*[一二三四五六七八九十百千\d]+\s*章|chapter\s+(?:\d+|[ivxlcdm]+)\b)",
    re.IGNORECASE,
)
FOCUSED_TOPIC_OR_SECTION_PATTERN = re.compile(
    r"(?:本文|这篇文章|这个文档|这份文档)\s*(?:中的|的)\s*"
    r"(?!主要内容|整体内容|核心内容|主题|概述|摘要|结论)\S+"
    r"|(?:this document|the document|this pdf|the pdf)(?:'s)?\s+"
    r"(?:section|part|chapter|topic)\b",
    re.IGNORECASE,
)


def is_document_overview_query(query: str) -> bool:
    """Return whether ``query`` asks for a broad document overview."""

    normalized_query = " ".join(query.strip().casefold().split())
    if not normalized_query or FOCUSED_CHAPTER_PATTERN.search(normalized_query):
        return False
    if FOCUSED_TOPIC_OR_SECTION_PATTERN.search(normalized_query):
        return False
    if any(phrase in normalized_query for phrase in IMPLICIT_DOCUMENT_OVERVIEWS):
        return True
    return any(reference in normalized_query for reference in DOCUMENT_REFERENCES) and any(
        request in normalized_query for request in OVERVIEW_REQUESTS
    )
