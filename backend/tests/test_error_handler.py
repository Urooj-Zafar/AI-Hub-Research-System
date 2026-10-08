import unittest

from backend.app.services.error_handler import (
    GroqConfigurationError,
    SimulatedProviderError,
    UnsupportedModelError,
    classify_error,
    is_retryable,
)


class ErrorHandlerTests(unittest.TestCase):
    def test_simulated_timeout_is_classified_and_retryable(self) -> None:
        error_type = classify_error(SimulatedProviderError("timeout"))
        self.assertEqual(error_type, "timeout")
        self.assertTrue(is_retryable(error_type))

    def test_missing_groq_configuration_is_not_reported_as_unknown(self) -> None:
        self.assertEqual(
            classify_error(GroqConfigurationError("not configured")),
            "authentication_error",
        )

    def test_unsupported_model_is_an_invalid_request(self) -> None:
        self.assertEqual(
            classify_error(UnsupportedModelError("unsupported")),
            "invalid_request",
        )

    def test_authentication_errors_are_not_retried(self) -> None:
        self.assertFalse(is_retryable("authentication_error"))


if __name__ == "__main__":
    unittest.main()
