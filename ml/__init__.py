"""Deterministic Career Quest recommendation engine."""

from .engine import (
    apply_event_gains,
    build_roadmap,
    calculate_skill_gap,
    event_is_eligible,
    recommend_activities,
    resolve_target,
)

__all__ = [
    "apply_event_gains",
    "build_roadmap",
    "calculate_skill_gap",
    "event_is_eligible",
    "recommend_activities",
    "resolve_target",
]
