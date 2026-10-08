"""Groq client, active-model verification, and controlled failure simulation."""

from __future__ import annotations

import asyncio
import os
import random
import time

from groq import AsyncGroq

from backend.app.core.config import (
    FAILURE_RATE,
    MODEL_LIST_CACHE_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    SIMULATE_FAILURE,
)
from backend.app.services.error_handler import (
    GroqConfigurationError,
    SimulatedProviderError,
    UnsupportedModelError,
)

_models_lock = asyncio.Lock()
_active_models: set[str] = set()
_models_checked_at = 0.0

SIMULATED_ERROR_TYPES = ("timeout", "rate_limit", "server_error", "network_error")


def create_groq_client() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqConfigurationError("GROQ_API_KEY is not configured.")
    # Internal SDK retries are disabled so retryCount and backoff only describe
    # the research mechanism implemented by this application.
    return AsyncGroq(
        api_key=api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )


async def ensure_model_supported(client: AsyncGroq, model_id: str) -> None:
    global _active_models, _models_checked_at
    now = time.monotonic()
    if now - _models_checked_at >= MODEL_LIST_CACHE_SECONDS:
        async with _models_lock:
            now = time.monotonic()
            if now - _models_checked_at >= MODEL_LIST_CACHE_SECONDS:
                response = await client.models.list()
                _active_models = {model.id for model in response.data}
                _models_checked_at = time.monotonic()
    if model_id not in _active_models:
        raise UnsupportedModelError(
            f"The configured model {model_id!r} is not active in the Groq model list."
        )


async def maybe_simulate_primary_failure() -> None:
    """Inject only explicitly enabled failures; the fallback still calls Groq."""
    if SIMULATE_FAILURE and random.random() < FAILURE_RATE:
        error_type = random.choice(SIMULATED_ERROR_TYPES)
        if error_type == "timeout":
            raise SimulatedProviderError("timeout")
        raise SimulatedProviderError(error_type)
