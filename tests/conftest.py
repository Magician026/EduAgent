from pathlib import Path

import fitz
import pytest


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def sample_pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Bayes Rule and MAP classification are core concepts.")
    page.insert_text((72, 110), "MAP chooses the class with the highest posterior probability.")
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.fixture()
def sample_empty_pdf_bytes() -> bytes:
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes
