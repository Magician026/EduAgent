"""Validated domain models shared by EduAgent services."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExplanationLevel(str, Enum):
    BEGINNER = "Beginner"
    STANDARD = "Standard"
    ADVANCED = "Advanced"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TeachingAction(str, Enum):
    EXPLAIN = "EXPLAIN"
    GIVE_EXAMPLE = "GIVE_EXAMPLE"
    ASK_DIAGNOSTIC_QUESTION = "ASK_DIAGNOSTIC_QUESTION"
    GENERATE_QUIZ = "GENERATE_QUIZ"
    REVIEW_PREREQUISITE = "REVIEW_PREREQUISITE"
    REMEDIATE_WEAK_CONCEPT = "REMEDIATE_WEAK_CONCEPT"
    INCREASE_DIFFICULTY = "INCREASE_DIFFICULTY"
    DECREASE_DIFFICULTY = "DECREASE_DIFFICULTY"
    CONTINUE_TOPIC = "CONTINUE_TOPIC"


class PageText(BaseModel):
    document_name: str
    document_hash: str
    page: int = Field(ge=1)
    text: str = Field(min_length=1)


class DocumentChunk(BaseModel):
    document_name: str
    document_hash: str
    page: int = Field(ge=1)
    chunk_id: str
    text: str = Field(min_length=1)


class RetrievedChunk(BaseModel):
    chunk: DocumentChunk
    similarity: float = Field(ge=-1.0, le=1.0)


class SourceReference(BaseModel):
    document_name: str
    page: int = Field(ge=1)
    chunk_id: str
    excerpt: str


class TutorResponse(BaseModel):
    answer: str = Field(min_length=1)
    sources: list[SourceReference] = Field(default_factory=list)


class QuizQuestion(BaseModel):
    question: str = Field(min_length=1)
    question_type: QuestionType
    concept: str = Field(min_length=1)
    difficulty: Difficulty
    options: list[str] = Field(default_factory=list)
    reference_answer: str = Field(min_length=1)
    source_chunks: list[str] = Field(default_factory=list)


class AnswerEvaluation(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    correct: bool
    feedback: str = Field(min_length=1)
    misconceptions: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    concept: str = Field(min_length=1)
    recommended_action: TeachingAction | None = None


class ConceptState(BaseModel):
    concept: str = Field(min_length=1)
    attempts: int = Field(ge=0)
    correct_attempts: int = Field(ge=0)
    average_score: float = Field(ge=0.0, le=1.0)
    mastery: float = Field(ge=0.0, le=1.0)
    last_score: float | None = Field(default=None, ge=0.0, le=1.0)
    last_practiced: datetime | None = None


class TeachingDecision(BaseModel):
    action: TeachingAction
    reason: str = Field(min_length=1)
    concept: str = Field(min_length=1)


class StudentProfile(BaseModel):
    student_id: str
    explanation_level: ExplanationLevel = ExplanationLevel.STANDARD


class OverviewMetrics(BaseModel):
    questions_asked: int = Field(ge=0)
    quizzes_completed: int = Field(ge=0)
    average_quiz_score: float = Field(ge=0.0, le=1.0)
    concepts_practiced: int = Field(ge=0)


class IndexedDocument(BaseModel):
    document_name: str
    document_hash: str
    page_count: int = Field(ge=1)
    chunk_count: int = Field(ge=1)
    indexed_at: datetime


class IngestionResult(BaseModel):
    status: str
    document_hash: str
    page_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    message: str
