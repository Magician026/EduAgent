import pytest

from eduagent.document_processing.parser import DocumentProcessingError, parse_pdf


def test_parser_preserves_one_based_page_numbers(sample_pdf_bytes):
    pages = parse_pdf("lesson.pdf", sample_pdf_bytes)

    assert pages[0].page == 1
    assert pages[0].document_name == "lesson.pdf"
    assert "Bayes" in pages[0].text


def test_parser_rejects_invalid_pdf():
    with pytest.raises(DocumentProcessingError, match="valid PDF"):
        parse_pdf("broken.pdf", b"not a PDF")


def test_parser_rejects_pdf_without_extractable_text(sample_empty_pdf_bytes):
    with pytest.raises(DocumentProcessingError, match="extractable text"):
        parse_pdf("empty.pdf", sample_empty_pdf_bytes)
