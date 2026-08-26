from datetime import UTC, datetime

import pytest

from eduagent.models import ConceptState
from eduagent.student.profile import (
    new_concept_state,
    update_concept_state,
    weak_concepts,
)

FIXED_NOW = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)


def test_first_attempt_uses_score_as_mastery():
    state = new_concept_state("Bayes Rule", score=0.8, correct=True, now=FIXED_NOW)

    assert state.mastery == pytest.approx(0.8)
    assert state.average_score == pytest.approx(0.8)
    assert state.attempts == 1
    assert state.correct_attempts == 1


def test_later_attempt_uses_transparent_weighting():
    previous = ConceptState(
        concept="Bayes Rule",
        attempts=1,
        correct_attempts=1,
        average_score=0.8,
        mastery=0.8,
        last_score=0.8,
        last_practiced=FIXED_NOW,
    )

    state = update_concept_state(previous, score=0.2, correct=False, now=FIXED_NOW)

    assert state.mastery == pytest.approx(0.70 * 0.8 + 0.30 * 0.2)
    assert state.average_score == pytest.approx(0.5)
    assert state.attempts == 2
    assert state.correct_attempts == 1


def test_invalid_score_is_rejected():
    with pytest.raises(ValueError, match="between 0 and 1"):
        update_concept_state(None, score=1.2, correct=True, now=FIXED_NOW)


def test_weak_concepts_are_sorted_by_mastery():
    states = [
        ConceptState(
            concept="Bayes Rule", attempts=1, correct_attempts=0,
            average_score=0.2, mastery=0.2, last_score=0.2,
        ),
        ConceptState(
            concept="MAP classification", attempts=1, correct_attempts=0,
            average_score=0.5, mastery=0.5, last_score=0.5,
        ),
        ConceptState(
            concept="Probability", attempts=1, correct_attempts=1,
            average_score=0.9, mastery=0.9, last_score=0.9,
        ),
    ]

    result = weak_concepts(states)

    assert [state.concept for state in result] == ["Bayes Rule", "MAP classification"]
