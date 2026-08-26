import pytest
from pydantic import ValidationError

from eduagent.models import DocumentChunk, PageText


def test_page_text_requires_positive_page_number():
    with pytest.raises(ValidationError):
        PageText(document_name="lesson.pdf", document_hash="hash", page=0, text="text")


def test_document_chunk_preserves_source_fields():
    chunk = DocumentChunk(
        document_name="lesson.pdf",
        document_hash="hash",
        page=2,
        chunk_id="hash-2-0",
        text="MAP classification",
    )
    assert chunk.page == 2
    assert chunk.chunk_id == "hash-2-0"
