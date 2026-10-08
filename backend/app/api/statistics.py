"""PostgreSQL-backed research aggregates and request history."""

from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, Query

from app.core.config import ERROR_TYPES, EXPERIMENT_MODES, TASK_TYPES
from app.database.database import get_pool
from app.models.request_model import (
    ErrorCount,
    ExperimentSummary,
    FallbackSummary,
    ModelCount,
    RequestList,
    RequestRecord,
    Statistics,
    TaskCount,
)

router = APIRouter()


@router.get("/statistics", response_model=Statistics)
async def get_statistics(pool: asyncpg.Pool = Depends(get_pool)) -> Statistics:
    async with pool.acquire() as connection:
        totals = await connection.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE NOT is_simulated)::int AS total,
                COUNT(*) FILTER (WHERE NOT is_simulated AND final_status = 'success')::int AS successful,
                COUNT(*) FILTER (WHERE NOT is_simulated AND final_status = 'failed')::int AS failed,
                COALESCE(AVG(response_time_ms) FILTER (WHERE NOT is_simulated), 0)::float8 AS average_ms,
                COALESCE(SUM(retry_count) FILTER (WHERE NOT is_simulated), 0)::int AS retries,
                COUNT(*) FILTER (WHERE NOT is_simulated AND fallback_used)::int AS fallback_events,
                COUNT(*) FILTER (WHERE NOT is_simulated AND fallback_used AND final_status = 'success')::int AS fallback_success,
                COUNT(*) FILTER (WHERE NOT is_simulated AND fallback_used AND final_status = 'failed')::int AS fallback_failed,
                COUNT(*) FILTER (WHERE is_simulated)::int AS simulated
            FROM ai_requests
            """
        )
        task_rows = await connection.fetch(
            """
            SELECT task_type, COUNT(*)::int AS count
            FROM ai_requests
            WHERE NOT is_simulated
            GROUP BY task_type
            """
        )
        model_rows = await connection.fetch(
            """
            SELECT model, COUNT(*)::int AS count
            FROM ai_requests
            WHERE NOT is_simulated AND model IS NOT NULL
            GROUP BY model
            ORDER BY count DESC, model
            """
        )
        error_rows = await connection.fetch(
            """
            SELECT error_type, COUNT(*)::int AS count
            FROM ai_requests
            WHERE NOT is_simulated AND error_type IS NOT NULL
            GROUP BY error_type
            """
        )
        mode_rows = await connection.fetch(
            """
            SELECT
                experiment_mode,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE final_status = 'success')::int AS successful,
                COUNT(*) FILTER (WHERE final_status = 'failed')::int AS failed,
                COALESCE(
                    100.0 * COUNT(*) FILTER (WHERE final_status = 'success')
                    / NULLIF(COUNT(*), 0),
                    0
                )::float8 AS success_rate,
                COALESCE(AVG(response_time_ms), 0)::float8 AS average_ms,
                COALESCE(SUM(retry_count), 0)::int AS retries,
                COUNT(*) FILTER (WHERE fallback_used)::int AS fallback_events
            FROM ai_requests
            WHERE NOT is_simulated
            GROUP BY experiment_mode
            """
        )
        task_counts = {row["task_type"]: row["count"] for row in task_rows}
        model_counts = {row["model"]: row["count"] for row in model_rows}
        error_counts = {row["error_type"]: row["count"] for row in error_rows}
        mode_counts = {row["experiment_mode"]: row for row in mode_rows}

    total = totals["total"]
    fallback_events = totals["fallback_events"]
    return Statistics(
        total_requests=total,
        successful_requests=totals["successful"],
        failed_requests=totals["failed"],
        success_rate=(100.0 * totals["successful"] / total) if total else 0.0,
        failure_rate=(100.0 * totals["failed"] / total) if total else 0.0,
        average_response_time_ms=totals["average_ms"],
        total_retries=totals["retries"],
        fallback=FallbackSummary(
            total_events=fallback_events,
            percentage=(100.0 * fallback_events / total) if total else 0.0,
            successful_responses=totals["fallback_success"],
            failed_responses=totals["fallback_failed"],
        ),
        task_distribution=[
            TaskCount(task_type=task, count=task_counts.get(task, 0))
            for task in TASK_TYPES
        ],
        model_usage=[
            ModelCount(model=model, count=count)
            for model, count in sorted(
                model_counts.items(), key=lambda pair: (-pair[1], pair[0])
            )
        ],
        error_analysis=[
            ErrorCount(error_type=error, count=error_counts.get(error, 0))
            for error in ERROR_TYPES
        ],
        experiment_comparison=[
            ExperimentSummary(
                experiment_mode=mode,  # type: ignore[arg-type]
                total_requests=mode_counts[mode]["total"] if mode in mode_counts else 0,
                successful_requests=mode_counts[mode]["successful"] if mode in mode_counts else 0,
                failed_requests=mode_counts[mode]["failed"] if mode in mode_counts else 0,
                success_rate=mode_counts[mode]["success_rate"] if mode in mode_counts else 0.0,
                average_response_time_ms=mode_counts[mode]["average_ms"] if mode in mode_counts else 0.0,
                total_retries=mode_counts[mode]["retries"] if mode in mode_counts else 0,
                fallback_events=mode_counts[mode]["fallback_events"] if mode in mode_counts else 0,
            )
            for mode in EXPERIMENT_MODES
        ],
        simulated_requests_excluded=totals["simulated"],
    )


@router.get("/requests", response_model=RequestList)
async def get_requests(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    experiment_mode: Literal["baseline", "proposed"] | None = Query(
        default=None,
        alias="experimentMode",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
) -> RequestList:
    async with pool.acquire() as connection:
        total = await connection.fetchval(
            """
            SELECT COUNT(*)::int
            FROM ai_requests
            WHERE $1::text IS NULL OR experiment_mode = $1
            """,
            experiment_mode,
        )
        rows = await connection.fetch(
            """
            SELECT id, task_type, experiment_mode, model,
                   primary_model, fallback_model, response_time_ms, retry_count,
                   error_type, fallback_used, final_status, is_simulated, created_at
            FROM ai_requests
            WHERE $1::text IS NULL OR experiment_mode = $1
            ORDER BY created_at DESC, id DESC
            LIMIT $2 OFFSET $3
            """,
            experiment_mode,
            limit,
            offset,
        )
    return RequestList(
        items=[RequestRecord.model_validate(dict(row)) for row in rows],
        total=total or 0,
        limit=limit,
        offset=offset,
    )
