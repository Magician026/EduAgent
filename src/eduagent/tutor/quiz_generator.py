"""Grounded structured quiz generation."""

from __future__ import annotations

from collections.abc import Sequence

from eduagent.llm.provider import LLMProvider
from eduagent.models import Difficulty, QuestionType, QuizQuestion


class QuizGenerator:
    """Generate one validated quiz question from retrieved course context."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(
        self,
        topic: str,
        question_type: QuestionType,
        difficulty: Difficulty,
        context: str,
        source_ids: Sequence[str],
    ) -> QuizQuestion:
        if not source_ids:
            raise ValueError("Quiz generation requires at least one retrieved source.")
        system = (
            "You are an educational quiz writer. Use only the supplied course context. "
            "Return one JSON object matching the QuizQuestion schema. Do not invent source IDs."
        )
        user = (
            f"Topic: {topic}\n"
            f"Question type: {question_type.value}\n"
            f"Difficulty: {difficulty.value}\n"
            f"Allowed source chunk IDs: {list(source_ids)}\nCourse context:\n{context}"
        )
        quiz = self.provider.complete_json(QuizQuestion, system, user, temperature=0.3)
        allowed = set(source_ids)
        if not set(quiz.source_chunks).issubset(allowed):
            raise ValueError("Quiz contains a source citation that was not retrieved.")
        if quiz.question_type is not question_type:
            raise ValueError("Quiz provider returned the wrong question type.")
        if quiz.difficulty is not difficulty:
            quiz = quiz.model_copy(update={"difficulty": difficulty})
        if not quiz.source_chunks:
            quiz = quiz.model_copy(update={"source_chunks": list(source_ids)})
        if question_type is QuestionType.MULTIPLE_CHOICE and len(quiz.options) < 2:
            raise ValueError("Multiple-choice quiz must contain at least two options.")
        return quiz
