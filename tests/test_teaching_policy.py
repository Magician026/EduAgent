from datetime import UTC, datetime

from eduagent.models import ConceptState, TeachingAction
from eduagent.tutor.teaching_policy import TeachingPolicy

NOW = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)


def _state(concept: str, mastery: float, last_score: float | None = None) -> ConceptState:
    return ConceptState(
        concept=concept,
        attempts=2,
        correct_attempts=1,
        average_score=mastery,
        mastery=mastery,
        last_score=last_score,
        last_practiced=NOW,
    )


def test_policy_explains_new_concept():
    decision = TeachingPolicy().choose("MAP classification", {}, recent_score=None)

    assert decision.action is TeachingAction.EXPLAIN


def test_policy_reviews_low_mastery():
    decision = TeachingPolicy().choose(
        "Bayes Rule",
        {"Bayes Rule": _state("Bayes Rule", mastery=0.2, last_score=0.2)},
        recent_score=0.2,
    )

    assert decision.action is TeachingAction.REVIEW_PREREQUISITE


def test_policy_gives_example_after_recent_incorrect_answer():
    decision = TeachingPolicy().choose(
        "MAP classification",
        {"MAP classification": _state("MAP classification", mastery=0.65, last_score=0.4)},
        recent_score=0.4,
    )

    assert decision.action is TeachingAction.GIVE_EXAMPLE


def test_policy_generates_quiz_for_developing_mastery():
    decision = TeachingPolicy().choose(
        "MAP classification",
        {"MAP classification": _state("MAP classification", mastery=0.65, last_score=0.8)},
        recent_score=0.8,
    )

    assert decision.action is TeachingAction.GENERATE_QUIZ


def test_policy_increases_difficulty_for_high_mastery():
    decision = TeachingPolicy().choose(
        "MAP classification",
        {"MAP classification": _state("MAP classification", mastery=0.9, last_score=0.9)},
        recent_score=0.9,
    )

    assert decision.action is TeachingAction.INCREASE_DIFFICULTY
