"""Transparent learner-model heuristics."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from eduagent.models import ConceptState


def update_concept_state(
    previous: ConceptState | None,
    score: float,
    correct: bool,
    now: datetime,
) -> ConceptState:
    """Update one concept with the documented weighted mastery heuristic."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be between 0 and 1")
    if previous is None:
        raise ValueError("A concept name is required for a new concept state")

    attempts = previous.attempts + 1
    average_score = ((previous.average_score * previous.attempts) + score) / attempts
    mastery = 0.70 * previous.mastery + 0.30 * score
    return previous.model_copy(
        update={
            "attempts": attempts,
            "correct_attempts": previous.correct_attempts + int(correct),
            "average_score": average_score,
            "mastery": mastery,
            "last_score": score,
            "last_practiced": now,
        }
    )


def new_concept_state(concept: str, score: float, correct: bool, now: datetime) -> ConceptState:
    """Create a state from the first attempt on a concept."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("score must be between 0 and 1")
    if not concept.strip():
        raise ValueError("concept must not be empty")
    return ConceptState(
        concept=concept.strip(),
        attempts=1,
        correct_attempts=int(correct),
        average_score=score,
        mastery=score,
        last_score=score,
        last_practiced=now,
    )


def weak_concepts(
    states: Iterable[ConceptState],
    threshold: float = 0.60,
) -> list[ConceptState]:
    """Return concepts below the transparent mastery threshold."""

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    return sorted(
        (state for state in states if state.mastery < threshold),
        key=lambda state: (state.mastery, state.concept.lower()),
    )
