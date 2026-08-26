import pytest

from eduagent.document_processing.chunker import chunk_pages
from eduagent.models import PageText


def test_chunker_preserves_page_metadata_and_overlap():
    pages = [PageText(document_name="x.pdf", document_hash="h", page=3, text="abcdefghij")]

    chunks = chunk_pages(pages, max_chars=6, overlap=2)

    assert all(chunk.page == 3 for chunk in chunks)
    assert chunks[0].chunk_id != chunks[1].chunk_id
    assert chunks[0].text[-2:] == chunks[1].text[:2]


def test_chunker_does_not_mix_pages():
    pages = [
        PageText(document_name="x.pdf", document_hash="h", page=1, text="page one"),
        PageText(document_name="x.pdf", document_hash="h", page=2, text="page two"),
    ]

    chunks = chunk_pages(pages, max_chars=100, overlap=10)

    assert [(chunk.page, chunk.text) for chunk in chunks] == [(1, "page one"), (2, "page two")]


def test_chunker_rejects_overlap_that_is_not_smaller_than_chunk_size():
    pages = [PageText(document_name="x.pdf", document_hash="h", page=1, text="text")]

    with pytest.raises(ValueError, match="overlap"):
        chunk_pages(pages, max_chars=10, overlap=10)
