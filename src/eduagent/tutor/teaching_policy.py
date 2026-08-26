"""Deterministic next-action policy for the tutor agent."""

from __future__ import annotations

from collections.abc import Mapping

from eduagent.models import ConceptState, TeachingAction, TeachingDecision


class TeachingPolicy:
    """Choose the next teaching action from transparent learner state rules."""

    def choose(
        self,
        concept: str,
        states: Mapping[str, ConceptState],
        recent_score: float | None,
    ) -> TeachingDecision:
        state = states.get(concept)
        if state is None:
            return TeachingDecision(
                action=TeachingAction.EXPLAIN,
                reason=(
                    "This concept has not been practiced yet, so EduAgent "
                    "starts with an explanation."
                ),
                concept=concept,
            )
        if state.mastery < 0.40:
            return TeachingDecision(
                action=TeachingAction.REVIEW_PREREQUISITE,
                reason=(
                    "Mastery is below 40%, so EduAgent recommends reviewing prerequisites first."
                ),
                concept=concept,
            )
        if recent_score is not None and recent_score < 0.50:
            return TeachingDecision(
                action=TeachingAction.GIVE_EXAMPLE,
                reason=(
                    "The latest score is below 50%, so EduAgent recommends "
                    "an example before another quiz."
                ),
                concept=concept,
            )
        if state.mastery < 0.75:
            return TeachingDecision(
                action=TeachingAction.GENERATE_QUIZ,
                reason=(
                    "Mastery is developing, so EduAgent recommends another "
                    "grounded practice question."
                ),
                concept=concept,
            )
        return TeachingDecision(
            action=TeachingAction.INCREASE_DIFFICULTY,
            reason="Mastery is above 75%, so EduAgent recommends increasing difficulty.",
            concept=concept,
        )
