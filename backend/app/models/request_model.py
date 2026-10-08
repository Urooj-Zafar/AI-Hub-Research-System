"""Validated JSON request and response shapes for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TaskType = Literal["Coding", "General Knowledge", "Reasoning", "Creative Writing"]
ExperimentMode = Literal["baseline", "proposed"]
ErrorType = Literal[
    "timeout",
    "rate_limit",
    "server_error",
    "network_error",
    "authentication_error",
    "invalid_request",
    "unknown_error",
]
FinalStatus = Literal["success", "failed"]


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


class ChatInput(ApiModel):
    message: str = Field(min_length=1, max_length=10_000)
    experiment_mode: ExperimentMode = "proposed"

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty.")
        return cleaned


class ChatResult(ApiModel):
    id: int
    success: bool
    response: str | None
    error_message: str | None
    task_type: TaskType
    experiment_mode: ExperimentMode
    model: str | None
    primary_model: str
    fallback_model: str
    fallback_used: bool
    retry_count: int
    response_time_ms: int
    error_type: ErrorType | None
    is_simulated: bool
    created_at: datetime


class RequestRecord(ApiModel):
    id: int
    task_type: TaskType
    experiment_mode: ExperimentMode
    model: str | None
    primary_model: str
    fallback_model: str
    response_time_ms: int
    retry_count: int
    error_type: ErrorType | None
    fallback_used: bool
    final_status: FinalStatus
    is_simulated: bool
    created_at: datetime


class RequestList(ApiModel):
    items: list[RequestRecord]
    total: int
    limit: int
    offset: int


class ApplicationInfo(ApiModel):
    name: str
    description: str
    version: str


class HealthStatus(ApiModel):
    status: str


class TaskCount(ApiModel):
    task_type: TaskType
    count: int


class ModelCount(ApiModel):
    model: str
    count: int


class ErrorCount(ApiModel):
    error_type: ErrorType
    count: int


class ExperimentSummary(ApiModel):
    experiment_mode: ExperimentMode
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time_ms: float
    total_retries: int
    fallback_events: int


class FallbackSummary(ApiModel):
    total_events: int
    percentage: float
    successful_responses: int
    failed_responses: int


class Statistics(ApiModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    failure_rate: float
    average_response_time_ms: float
    total_retries: int
    fallback: FallbackSummary
    task_distribution: list[TaskCount]
    model_usage: list[ModelCount]
    error_analysis: list[ErrorCount]
    experiment_comparison: list[ExperimentSummary]
    simulated_requests_excluded: int
