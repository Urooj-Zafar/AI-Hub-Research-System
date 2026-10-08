"""Chat orchestration, measured execution, resilience, and PostgreSQL logging."""

from __future__ import annotations

import asyncio
import logging
import time
import asyncpg
from groq import AsyncGroq

from app.core.config import (
    BASE_DELAY_SECONDS,
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
)
from    app.models.request_model import ChatResult
from app.services.error_handler import (
    GroqConfigurationError,
    SimulatedProviderError,
    classify_error,
    is_retryable,
    user_facing_error,
)
from app.services.groq_service import (
    create_groq_client,
    ensure_model_supported,
    maybe_simulate_primary_failure,
)
from app.services.model_selector import classify_task, select_models

logger = logging.getLogger("ai_hub")


async def _call_model(client: AsyncGroq, model_id: str, message: str) -> str:
    await ensure_model_supported(client, model_id)
    result = await client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": "Answer clearly and accurately. If a request is ambiguous, state the assumption you use.",
            },
            {"role": "user", "content": message},
        ],
        max_tokens=2048,
    )
    content = result.choices[0].message.content
    return content or ""


async def execute_chat(
    pool: asyncpg.Pool,
    message: str,
    experiment_mode: str,
) -> ChatResult:
    task_type = classify_task(message)
    primary_model, fallback_model = select_models(task_type, experiment_mode)
    started_at = time.perf_counter()
    retry_count = 0
    fallback_used = False
    is_simulated = False
    last_error_type: str | None = None
    final_response: str | None = None
    final_model: str | None = None

    try:
        client = create_groq_client()
    except GroqConfigurationError as exc:
        client = None
        last_error_type = classify_error(exc)

    if client is not None:
        while True:
            try:
                await maybe_simulate_primary_failure()
                final_response = await asyncio.wait_for(
                    _call_model(client, primary_model, message),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                final_model = primary_model
                break
            except Exception as exc:
                last_error_type = classify_error(exc)
                is_simulated = is_simulated or isinstance(exc, SimulatedProviderError)
                logger.warning(
                    "Primary model attempt failed: model=%s error_type=%s retry=%s simulated=%s",
                    primary_model,
                    last_error_type,
                    retry_count,
                    is_simulated,
                )
                if (
                    experiment_mode != "proposed"
                    or not is_retryable(last_error_type)
                    or retry_count >= MAX_RETRIES
                ):
                    break
                delay = BASE_DELAY_SECONDS * (2**retry_count)
                retry_count += 1
                await asyncio.sleep(delay)

        if final_response is None and experiment_mode == "proposed":
            fallback_used = True
            try:
                final_response = await asyncio.wait_for(
                    _call_model(client, fallback_model, message),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                final_model = fallback_model
            except Exception as exc:
                last_error_type = classify_error(exc)
                is_simulated = is_simulated or isinstance(exc, SimulatedProviderError)
                logger.warning(
                    "Fallback model attempt failed: model=%s error_type=%s simulated=%s",
                    fallback_model,
                    last_error_type,
                    is_simulated,
                )

    response_time_ms = max(0, int((time.perf_counter() - started_at) * 1000))
    success = final_response is not None
    final_status = "success" if success else "failed"

    try:
        row = await pool.fetchrow(
            """
            INSERT INTO ai_requests (
                user_query, task_type, experiment_mode, model, primary_model,
                fallback_model, response_time_ms, retry_count, error_type,
                fallback_used, final_status, is_simulated
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id, created_at
            """,
            message,
            task_type,
            experiment_mode,
            final_model,
            primary_model,
            fallback_model,
            response_time_ms,
            retry_count,
            last_error_type,
            fallback_used,
            final_status,
            is_simulated,
        )
    except Exception:
        logger.exception("Could not store AI request in PostgreSQL.")
        raise

    error_message = None if success else user_facing_error(
        last_error_type or "unknown_error"
    )
    if not success and is_simulated:
        error_message = (
            "This controlled test attempt failed and was saved separately from "
            "the real-experiment statistics."
        )

    return ChatResult(
        id=row["id"],
        success=success,
        response=final_response,
        error_message=error_message,
        task_type=task_type,  # type: ignore[arg-type]
        experiment_mode=experiment_mode,  # type: ignore[arg-type]
        model=final_model,
        primary_model=primary_model,
        fallback_model=fallback_model,
        fallback_used=fallback_used,
        retry_count=retry_count,
        response_time_ms=response_time_ms,
        error_type=last_error_type,  # type: ignore[arg-type]
        is_simulated=is_simulated,
        created_at=row["created_at"],
    )


