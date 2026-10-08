"""Transparent rule-based task classification and deterministic model routing."""

from __future__ import annotations

import re

from backend.app.core.config import BASELINE_MODEL, FALLBACK_MODEL, TASK_MODELS

CODING_PATTERN = re.compile(
    r"\b(code|coding|program|algorithm|function|debug|bug|script|javascript|"
    r"typescript|python|java|sql|html|css|react|api|implement|compile)\b",
    re.IGNORECASE,
)
CREATIVE_PATTERN = re.compile(
    r"\b(story|short story|poem|poetry|creative writing|fiction|narrative|"
    r"screenplay|dialogue|lyrics|compose|draft)\b",
    re.IGNORECASE,
)
REASONING_PATTERN = re.compile(
    r"\b(reason|reasoning|logic|solve|calculate|prove|deduce|compare|"
    r"step by step|analyze|analyse|greater than|greatest|less than|least|"
    r"larger than|smallest|largest|if .{1,80} then)\b",
    re.IGNORECASE,
)


def classify_task(message: str) -> str:
    """Apply visible keyword rules in order; unmatched queries default to knowledge."""
    if CODING_PATTERN.search(message):
        return "Coding"
    if CREATIVE_PATTERN.search(message):
        return "Creative Writing"
    if REASONING_PATTERN.search(message):
        return "Reasoning"
    return "General Knowledge"


def select_models(task_type: str, experiment_mode: str) -> tuple[str, str]:
    """Return the fixed baseline or category-specific proposed model and fallback."""
    if experiment_mode == "baseline":
        return BASELINE_MODEL, FALLBACK_MODEL
    return TASK_MODELS.get(task_type, TASK_MODELS["General Knowledge"]), FALLBACK_MODEL
