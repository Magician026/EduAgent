from pathlib import Path

import fitz
import pytest

from eduagent.models import AnswerEvaluation, Difficulty, QuestionType, QuizQuestion


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


@pytest.fixture()
def quiz() -> QuizQuestion:
    return QuizQuestion(
        question="What does MAP classification choose?",
        question_type=QuestionType.SHORT_ANSWER,
        concept="MAP classification",
        difficulty=Difficulty.MEDIUM,
        reference_answer="The class with the highest posterior probability.",
        source_chunks=["sample-1"],
    )


@pytest.fixture()
def evaluation() -> AnswerEvaluation:
    return AnswerEvaluation(
        score=0.4,
        correct=False,
        feedback="You identified the concept but omitted posterior probability.",
        missing_points=["highest posterior probability"],
        concept="MAP classification",
    )
