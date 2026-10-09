
"""Groq client, active-model verification, and controlled failure simulation."""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time

from groq import AsyncGroq

from app.core.config import (
    FAILURE_RATE,
    MODEL_LIST_CACHE_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    SIMULATE_FAILURE,
)
from app.services.error_handler import (
    GroqConfigurationError,
    SimulatedProviderError,
    UnsupportedModelError,
)

logger = logging.getLogger("ai_hub")

_models_lock = asyncio.Lock()
_active_models: set[str] = set()
_models_checked_at = 0.0

SIMULATED_ERROR_TYPES = ("timeout", "rate_limit", "server_error", "network_error")


def create_groq_client() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqConfigurationError("GROQ_API_KEY is not configured.")

    return AsyncGroq(
        api_key=api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )


async def ensure_model_supported(client: AsyncGroq, model_id: str) -> None:
    """Refresh Groq's model list and verify the configured model ID."""
    global _active_models, _models_checked_at

    async with _models_lock:
        now = time.monotonic()

        if now - _models_checked_at >= MODEL_LIST_CACHE_SECONDS:
            response = await client.models.list()
            _active_models = {model.id for model in response.data}
            _models_checked_at = time.monotonic()

        # Refresh once if the configured model isn't in the cached list.
        if model_id not in _active_models:
            response = await client.models.list()
            _active_models = {model.id for model in response.data}
            _models_checked_at = time.monotonic()

        if model_id not in _active_models:
            logger.error(
                "Configured model %r not found in Groq model list. "
                "Available IDs: %s",
                model_id,
                sorted(_active_models),
            )
            raise UnsupportedModelError(
                f"Configured model {model_id!r} is not present in "
                "the active models returned by the Groq API."
            )


async def maybe_simulate_primary_failure() -> None:
    """Inject only explicitly enabled failures; fallback still calls Groq."""
    if SIMULATE_FAILURE and random.random() < FAILURE_RATE:
        error_type = random.choice(SIMULATED_ERROR_TYPES)

        if error_type == "timeout":
            raise SimulatedProviderError("timeout")

        raise SimulatedProviderError(error_type)