"""SQLite persistence for the single-student MVP."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eduagent.models import (
    AnswerEvaluation,
    ConceptState,
    ExplanationLevel,
    IndexedDocument,
    OverviewMetrics,
    QuizQuestion,
    StudentProfile,
)
from eduagent.student.profile import new_concept_state, update_concept_state, weak_concepts


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class StudentRepository:
    """Persist profile, concept mastery, activity, and document manifests in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the MVP schema idempotently."""

        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    student_id TEXT PRIMARY KEY,
                    explanation_level TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS concept_states (
                    student_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    correct_attempts INTEGER NOT NULL,
                    average_score REAL NOT NULL,
                    mastery REAL NOT NULL,
                    last_score REAL,
                    last_practiced TEXT,
                    PRIMARY KEY (student_id, concept)
                );
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    question_json TEXT NOT NULL,
                    submitted_answer TEXT NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    score REAL NOT NULL,
                    correct INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS documents (
                    document_hash TEXT PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL
                );
                """
            )

    def get_profile(self, student_id: str) -> StudentProfile:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT student_id, explanation_level FROM student_profiles WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            if row is None:
                now = _utc_now().isoformat()
                connection.execute(
                    """
                    INSERT INTO student_profiles(
                        student_id, explanation_level, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, ExplanationLevel.STANDARD.value, now, now),
                )
                return StudentProfile(
                    student_id=student_id,
                    explanation_level=ExplanationLevel.STANDARD,
                )
            return StudentProfile(
                student_id=row["student_id"],
                explanation_level=ExplanationLevel(row["explanation_level"]),
            )

    def set_explanation_level(self, student_id: str, level: ExplanationLevel) -> None:
        self.get_profile(student_id)
        with self._connect() as connection:
            connection.execute(
                (
                    "UPDATE student_profiles SET explanation_level = ?, updated_at = ? "
                    "WHERE student_id = ?"
                ),
                (level.value, _utc_now().isoformat(), student_id),
            )

    def record_interaction(self, student_id: str, question: str, answer: str) -> None:
        self.get_profile(student_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO interactions(student_id, question, answer, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, question, answer, _utc_now().isoformat()),
            )

    @staticmethod
    def _state_from_row(row: sqlite3.Row) -> ConceptState:
        return ConceptState(
            concept=row["concept"],
            attempts=row["attempts"],
            correct_attempts=row["correct_attempts"],
            average_score=row["average_score"],
            mastery=row["mastery"],
            last_score=row["last_score"],
            last_practiced=_parse_datetime(row["last_practiced"]),
        )

    def _get_state(
        self,
        connection: sqlite3.Connection,
        student_id: str,
        concept: str,
    ) -> ConceptState | None:
        row = connection.execute(
            "SELECT * FROM concept_states WHERE student_id = ? AND concept = ?",
            (student_id, concept),
        ).fetchone()
        return self._state_from_row(row) if row else None

    def record_attempt(
        self,
        student_id: str,
        quiz: QuizQuestion,
        submitted_answer: str,
        evaluation: AnswerEvaluation,
    ) -> ConceptState:
        """Persist a quiz attempt and atomically update its concept state."""

        self.get_profile(student_id)
        now = _utc_now()
        with self._connect() as connection:
            previous = self._get_state(connection, student_id, evaluation.concept)
            state = (
                new_concept_state(evaluation.concept, evaluation.score, evaluation.correct, now)
                if previous is None
                else update_concept_state(previous, evaluation.score, evaluation.correct, now)
            )
            connection.execute(
                """
                INSERT INTO concept_states(
                    student_id, concept, attempts, correct_attempts, average_score,
                    mastery, last_score, last_practiced
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, concept) DO UPDATE SET
                    attempts = excluded.attempts,
                    correct_attempts = excluded.correct_attempts,
                    average_score = excluded.average_score,
                    mastery = excluded.mastery,
                    last_score = excluded.last_score,
                    last_practiced = excluded.last_practiced
                """,
                (
                    student_id,
                    state.concept,
                    state.attempts,
                    state.correct_attempts,
                    state.average_score,
                    state.mastery,
                    state.last_score,
                    state.last_practiced.isoformat() if state.last_practiced else None,
                ),
            )
            connection.execute(
                """
                INSERT INTO quiz_attempts(
                    student_id, concept, question_json, submitted_answer,
                    evaluation_json, score, correct, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    quiz.concept,
                    json.dumps(quiz.model_dump(mode="json"), ensure_ascii=False),
                    submitted_answer,
                    json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False),
                    evaluation.score,
                    int(evaluation.correct),
                    now.isoformat(),
                ),
            )
        return state

    def list_concept_states(self, student_id: str) -> list[ConceptState]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                (
                    "SELECT * FROM concept_states WHERE student_id = ? "
                    "ORDER BY mastery ASC, concept ASC"
                ),
                (student_id,),
            ).fetchall()
        return [self._state_from_row(row) for row in rows]

    def list_weak_concepts(self, student_id: str) -> list[ConceptState]:
        return weak_concepts(self.list_concept_states(student_id))

    def overview(self, student_id: str) -> OverviewMetrics:
        self.initialize()
        with self._connect() as connection:
            questions = connection.execute(
                "SELECT COUNT(*) FROM interactions WHERE student_id = ?", (student_id,)
            ).fetchone()[0]
            quiz_row = connection.execute(
                "SELECT COUNT(*) AS count, COALESCE(AVG(score), 0.0) AS average "
                "FROM quiz_attempts WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            concepts = connection.execute(
                "SELECT COUNT(*) FROM concept_states WHERE student_id = ?", (student_id,)
            ).fetchone()[0]
        return OverviewMetrics(
            questions_asked=questions,
            quizzes_completed=quiz_row["count"],
            average_quiz_score=quiz_row["average"],
            concepts_practiced=concepts,
        )

    def document_exists(self, document_hash: str) -> bool:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM documents WHERE document_hash = ?", (document_hash,)
            ).fetchone()
        return row is not None

    def register_document(
        self,
        document_name: str,
        document_hash: str,
        page_count: int,
        chunk_count: int,
    ) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO documents(
                    document_hash, document_name, page_count, chunk_count, indexed_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (document_hash, document_name, page_count, chunk_count, _utc_now().isoformat()),
            )

    def list_documents(self) -> list[IndexedDocument]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY indexed_at DESC").fetchall()
        return [
            IndexedDocument(
                document_name=row["document_name"],
                document_hash=row["document_hash"],
                page_count=row["page_count"],
                chunk_count=row["chunk_count"],
                indexed_at=datetime.fromisoformat(row["indexed_at"]),
            )
            for row in rows
        ]

    def recent_attempts(self, student_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent quiz summaries for the Progress page."""

        if limit < 1:
            return []
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT concept, score, correct, created_at
                FROM quiz_attempts
                WHERE student_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (student_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]
