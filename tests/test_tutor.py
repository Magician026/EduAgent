from dataclasses import dataclass, field

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
    complete_text_calls: list[tuple[str, str]] = field(default_factory=list)

    def complete_text(self, system, user, *, temperature=0.2):
        self.complete_text_calls.append((system, user))
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
        self.overview_results = [
            RetrievedChunk(
                chunk=DocumentChunk(
                    document_name="lecture_05.pdf",
                    document_hash="hash",
                    page=10,
                    chunk_id="contents-1",
                    text="Contents: MAP classification and posterior probability.",
                ),
                similarity=0.0,
            )
        ]
        self.focused_calls = 0
        self.overview_calls = 0

    def retrieve(self, query, k=None):
        self.focused_calls += 1
        return self.results

    def retrieve_document_overview(self):
        self.overview_calls += 1
        return self.overview_results

    def format_context(self, results):
        return "\n\n---\n\n".join(
            "\n".join(
                [
                    f"Source: {result.chunk.document_name} — Page {result.chunk.page}",
                    f"Chunk ID: {result.chunk.chunk_id}",
                    result.chunk.text,
                ]
            )
            for result in results
        )


def test_tutor_attaches_retrieved_sources():
    retriever = FakeRetriever()
    provider = FakeProvider()
    tutor = TutorAgent(provider, retriever, TeachingPolicy())

    response = tutor.answer_question(
        "What is MAP classification?", ExplanationLevel.STANDARD, []
    )

    assert response.answer.startswith("MAP classification")
    assert response.sources[0].page == 12
    assert response.sources[0].document_name == "lecture_05.pdf"
    assert retriever.focused_calls == 1
    assert retriever.overview_calls == 0
    system, user = provider.complete_text_calls[0]
    assert system == (
        "You are EduAgent, a course-grounded university tutor. Use the supplied context "
        "as evidence, explain at the requested level, do not invent citations, and say "
        "when the context is insufficient."
    )
    assert "Retrieved course context:" in user
    assert "Page 12" in user
    assert "MAP classification selects the highest posterior class." in user


def test_tutor_routes_broad_question_to_document_overview():
    retriever = FakeRetriever()
    provider = FakeProvider()
    tutor = TutorAgent(provider, retriever, TeachingPolicy())

    response = tutor.answer_question(
        "帮我介绍一下这个pdf讲了什么内容",
        ExplanationLevel.STANDARD,
        [],
    )

    assert retriever.overview_calls == 1
    assert retriever.focused_calls == 0
    assert response.sources[0].page == 10
    system, user = provider.complete_text_calls[0]
    assert "Explain the document's purpose" in system
    assert "Page 10" in user
    assert "Contents: MAP classification and posterior probability." in user


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
