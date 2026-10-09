"""Single source of truth for models and resilience settings."""

from __future__ import annotations

import os


APP_NAME = "AI Hub Research System"
APP_DESCRIPTION = (
    "A research workspace for comparing task-based model selection "
    "and resilient AI request handling."
)
APP_VERSION = "1.0.0"

# Model identifiers are checked against Groq's active models list before use.
# Keep all model names here so they can be changed in one place.
TASK_MODELS = {
    "Coding": os.getenv("GROQ_MODEL_CODING", "qwen/qwen3.8-27b"),
    "General Knowledge": os.getenv("GROQ_MODEL_GENERAL", "openai/gpt-oss-20b"),
    "Reasoning": os.getenv("GROQ_MODEL_REASONING", "openai/gpt-oss-120b"),
    "Creative Writing": os.getenv("GROQ_MODEL_CREATIVE", "qwen/qwen3.8-27b"),
}
BASELINE_MODEL = os.getenv("GROQ_BASELINE_MODEL", "openai/gpt-oss-20b")
FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-2.5-flash-lite",
)

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
BASE_DELAY_SECONDS = float(os.getenv("RETRY_BASE_DELAY_SECONDS", "0.25"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))
MODEL_LIST_CACHE_SECONDS = 300

SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE", "false").strip().lower() == "true"
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0"))

TASK_TYPES = ("Coding", "General Knowledge", "Reasoning", "Creative Writing")
ERROR_TYPES = (
    "timeout",
    "rate_limit",
    "server_error",
    "network_error",
    "authentication_error",
    "invalid_request",
    "unknown_error",
)
EXPERIMENT_MODES = ("baseline", "proposed")

if MAX_RETRIES < 0:
    raise ValueError("MAX_RETRIES must be 0 or greater.")
if BASE_DELAY_SECONDS < 0:
    raise ValueError("RETRY_BASE_DELAY_SECONDS must be 0 or greater.")
if REQUEST_TIMEOUT_SECONDS <= 0:
    raise ValueError("GROQ_TIMEOUT_SECONDS must be greater than 0.")
if not 0 <= FAILURE_RATE <= 1:
    raise ValueError("FAILURE_RATE must be between 0 and 1.")
