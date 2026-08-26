from dataclasses import dataclass

from eduagent.models import (
    AnswerEvaluation,
    Difficulty,
    DocumentChunk,
    ExplanationLevel,
    QuestionType,
    QuizQuestion,
    RetrievedChunk,
    TeachingAction,
)
from eduagent.tutor.quiz_generator import QuizGenerator
from eduagent.tutor.teaching_policy import TeachingPolicy
from eduagent.tutor.tutor_agent import TutorAgent


@dataclass
class FakeProvider:
    def complete_text(self, system, user, *, temperature=0.2):
        return "MAP classification selects the class with the highest posterior probability."

    def complete_json(self, model_type, system, user, *, temperature=0.2):
        if model_type is QuizQuestion:
            return QuizQuestion(
                question="What does MAP classification select?",
                question_type=QuestionType.SHORT_ANSWER,
                concept="MAP classification",
                difficulty=Difficulty.MEDIUM,
                reference_answer="The class with the highest posterior probability.",
                source_chunks=["chunk-1"],
            )
        return AnswerEvaluation(
            score=0.8,
            correct=True,
            feedback="The answer captures the key idea.",
            concept="MAP classification",
        )


class FakeRetriever:
    def __init__(self):
        self.results = [
            RetrievedChunk(
                chunk=DocumentChunk(
                    document_name="lecture_05.pdf",
                    document_hash="hash",
                    page=12,
                    chunk_id="chunk-1",
                    text="MAP classification selects the highest posterior class.",
                ),
                similarity=0.9,
            )
        ]

    def retrieve(self, query, k=None):
        return self.results

    def format_context(self, results):
        return (
            "Source: lecture_05.pdf — Page 12\n"
            "MAP classification selects the highest posterior class."
        )


def test_tutor_attaches_retrieved_sources():
    tutor = TutorAgent(FakeProvider(), FakeRetriever(), TeachingPolicy())

    response = tutor.answer_question(
        "What is MAP classification?", ExplanationLevel.STANDARD, []
    )

    assert response.answer.startswith("MAP classification")
    assert response.sources[0].page == 12
    assert response.sources[0].document_name == "lecture_05.pdf"


def test_quiz_generator_rejects_unknown_source_ids():
    class BadProvider(FakeProvider):
        def complete_json(self, model_type, system, user, *, temperature=0.2):
            quiz = super().complete_json(model_type, system, user, temperature=temperature)
            return quiz.model_copy(update={"source_chunks": ["invented-source"]})

    generator = QuizGenerator(BadProvider())

    try:
        generator.generate(
            "MAP classification",
            QuestionType.SHORT_ANSWER,
            Difficulty.MEDIUM,
            "MAP context",
            ["chunk-1"],
        )
    except ValueError as exc:
        assert "source" in str(exc).lower()
    else:
        raise AssertionError("unknown source ID should be rejected")


def test_tutor_evaluation_returns_policy_decision():
    tutor = TutorAgent(FakeProvider(), FakeRetriever(), TeachingPolicy())
    quiz = FakeProvider().complete_json(QuizQuestion, "", "")

    evaluation, decision = tutor.evaluate_answer(quiz, "The highest posterior class", [])

    assert evaluation.score == 0.8
    assert decision.action is TeachingAction.EXPLAIN
