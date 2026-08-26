"""Structured formative answer evaluation."""

from __future__ import annotations

from eduagent.llm.provider import LLMProvider
from eduagent.models import AnswerEvaluation, QuizQuestion


class AnswerEvaluator:
    """Evaluate a student answer against a grounded quiz reference answer."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def evaluate(
        self,
        quiz: QuizQuestion,
        submitted_answer: str,
        context: str,
    ) -> AnswerEvaluation:
        system = (
            "You are providing automated formative feedback, not an official grade. "
            "Compare the student's answer with the reference answer and course context. "
            "Return one JSON object matching the AnswerEvaluation schema."
        )
        user = (
            f"Concept: {quiz.concept}\nReference answer: {quiz.reference_answer}\n"
            f"Student answer: {submitted_answer}\nCourse context:\n{context}"
        )
        evaluation = self.provider.complete_json(AnswerEvaluation, system, user, temperature=0.0)
        if evaluation.concept != quiz.concept:
            evaluation = evaluation.model_copy(update={"concept": quiz.concept})
        return evaluation
