"""Provider error classification and retry policy."""

from __future__ import annotations

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

ErrorKind = str
RETRYABLE_ERRORS = {"timeout", "rate_limit", "server_error", "network_error"}


class SimulatedProviderError(Exception):
    """A marked test-only failure; never mistaken for an actual Groq failure."""

    def __init__(self, error_type: ErrorKind) -> None:
        super().__init__("Controlled failure simulation")
        self.error_type = error_type


class GroqConfigurationError(Exception):
    """Safe, actionable error for missing credentials or unsupported models."""


class UnsupportedModelError(GroqConfigurationError):
    """The configured model is not in Groq's currently active model list."""


def classify_error(error: Exception) -> ErrorKind:
    if isinstance(error, SimulatedProviderError):
        return error.error_type
    if isinstance(error, UnsupportedModelError):
        return "invalid_request"
    if isinstance(error, GroqConfigurationError):
        return "authentication_error"
    if isinstance(error, (APITimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(error, RateLimitError):
        return "rate_limit"
    if isinstance(error, InternalServerError):
        return "server_error"
    if isinstance(error, APIConnectionError):
        return "network_error"
    if isinstance(error, AuthenticationError):
        return "authentication_error"
    if isinstance(error, BadRequestError):
        return "invalid_request"
    if isinstance(error, APIStatusError):
        if error.status_code == 429:
            return "rate_limit"
        if error.status_code >= 500:
            return "server_error"
        if error.status_code in {400, 404, 422}:
            return "invalid_request"
        if error.status_code in {401, 403}:
            return "authentication_error"
    return "unknown_error"


def is_retryable(error_type: ErrorKind) -> bool:
    return error_type in RETRYABLE_ERRORS


def user_facing_error(error_type: ErrorKind) -> str:
    messages = {
        "timeout": "The AI provider took too long to respond. The attempt was recorded.",
        "rate_limit": "The AI provider is temporarily rate-limited. The attempt was recorded.",
        "server_error": "The AI provider had a temporary service problem. The attempt was recorded.",
        "network_error": "The AI provider could not be reached. The attempt was recorded.",
        "authentication_error": "Groq credentials need attention. Check the GROQ_API_KEY secret.",
        "invalid_request": "The configured model or request is not accepted by Groq. Review model settings.",
        "unknown_error": "The AI request could not be completed. The attempt was recorded.",
    }
    return messages.get(error_type, messages["unknown_error"])
