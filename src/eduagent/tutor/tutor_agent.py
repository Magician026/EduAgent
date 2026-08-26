"""Composition layer for grounded tutoring and adaptive practice."""

from __future__ import annotations

from collections.abc import Sequence

from eduagent.llm.provider import LLMProvider
from eduagent.models import (
    AnswerEvaluation,
    Difficulty,
    ExplanationLevel,
    QuestionType,
    QuizQuestion,
    SourceReference,
    TeachingDecision,
    TutorResponse,
)
from eduagent.tutor.answer_evaluator import AnswerEvaluator
from eduagent.tutor.quiz_generator import QuizGenerator
from eduagent.tutor.teaching_policy import TeachingPolicy


class NoRelevantContextError(RuntimeError):
    """Raised when a content-generation action has no course evidence."""


class TutorAgent:
    """Use retrieval and an LLM for content while retaining deterministic policy control."""

    def __init__(
        self,
        provider: LLMProvider,
        retriever,
        policy: TeachingPolicy,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.policy = policy
        self.quiz_generator = QuizGenerator(provider)
        self.answer_evaluator = AnswerEvaluator(provider)

    def answer_question(
        self,
        question: str,
        level: ExplanationLevel,
        profile: Sequence,
    ) -> TutorResponse:
        results = self.retriever.retrieve(question)
        if not results:
            return TutorResponse(
                answer=(
                    "I could not find enough evidence in the indexed course materials. "
                    "Please upload and index the relevant lecture notes."
                )
            )
        system = (
            "You are EduAgent, a course-grounded university tutor. Use the supplied context "
            "as evidence, explain at the requested level, do not invent citations, and say "
            "when the context is insufficient."
        )
        user = (
            f"Explanation level: {level.value}\nStudent question: {question}\n"
            f"Retrieved course context:\n{self.retriever.format_context(results)}"
        )
        answer = self.provider.complete_text(system, user, temperature=0.2)
        sources = [
            SourceReference(
                document_name=result.chunk.document_name,
                page=result.chunk.page,
                chunk_id=result.chunk.chunk_id,
                excerpt=result.chunk.text[:320],
            )
            for result in results
        ]
        return TutorResponse(answer=answer, sources=sources)

    def generate_quiz(
        self,
        topic: str,
        question_type: QuestionType,
        difficulty: Difficulty,
        profile: Sequence,
    ) -> QuizQuestion:
        results = self.retriever.retrieve(topic)
        if not results:
            raise NoRelevantContextError(
                "No relevant course material was retrieved for this topic."
            )
        return self.quiz_generator.generate(
            topic,
            question_type,
            difficulty,
            self.retriever.format_context(results),
            [result.chunk.chunk_id for result in results],
        )

    def evaluate_answer(
        self,
        quiz: QuizQuestion,
        submitted_answer: str,
        profile: Sequence,
    ) -> tuple[AnswerEvaluation, TeachingDecision]:
        results = self.retriever.retrieve(quiz.question)
        context = self.retriever.format_context(results)
        evaluation = self.answer_evaluator.evaluate(quiz, submitted_answer, context)
        states = {state.concept: state for state in profile}
        decision = self.policy.choose(evaluation.concept, states, recent_score=evaluation.score)
        return evaluation, decision
