"""Page-aware PDF text extraction."""

from __future__ import annotations

import hashlib
import re

import fitz

from eduagent.models import PageText


class DocumentProcessingError(RuntimeError):
    """A user-correctable PDF processing failure."""


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(file_name: str, pdf_bytes: bytes) -> list[PageText]:
    """Extract non-empty page text while preserving one-based page numbers."""

    if not pdf_bytes:
        raise DocumentProcessingError("The uploaded file is not a valid PDF.")

    document_hash = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except (fitz.FileDataError, ValueError, RuntimeError) as exc:
        raise DocumentProcessingError("The uploaded file is not a valid PDF.") from exc

    pages: list[PageText] = []
    try:
        for page_index, page in enumerate(document):
            text = _clean_text(page.get_text("text"))
            if text:
                pages.append(
                    PageText(
                        document_name=file_name,
                        document_hash=document_hash,
                        page=page_index + 1,
                        text=text,
                    )
                )
    finally:
        document.close()

    if not pages:
        raise DocumentProcessingError("The PDF contains no extractable text.")
    return pages
