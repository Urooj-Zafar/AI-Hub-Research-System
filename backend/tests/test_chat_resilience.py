import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.services.chat_service import execute_chat
from app.services.error_handler import SimulatedProviderError


class FakePool:
    def __init__(self) -> None:
        self.inserted_values = None

    async def fetchrow(self, _query: str, *values: object) -> dict[str, object]:
        self.inserted_values = values
        return {"id": 7, "created_at": datetime.now(timezone.utc)}


class ChatResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def test_proposed_mode_retries_then_succeeds_and_records_retry(self) -> None:
        pool = FakePool()
        with (
            patch("backend.app.services.chat_service.create_groq_client", return_value=object()),
            patch("backend.app.services.chat_service.maybe_simulate_primary_failure", new_callable=AsyncMock),
            patch(
                "backend.app.services.chat_service.asyncio.sleep",
                new_callable=AsyncMock,
            ) as sleep_mock,
            patch(
                "backend.app.services.chat_service._call_model",
                new_callable=AsyncMock,
                side_effect=[SimulatedProviderError("rate_limit"), "Recovered answer"],
            ) as call_model,
        ):
            result = await execute_chat(pool, "Write a Python function.", "proposed")

        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 1)
        self.assertEqual(result.error_type, "rate_limit")
        self.assertEqual(result.response, "Recovered answer")
        self.assertTrue(result.is_simulated)
        self.assertEqual(call_model.await_count, 2)
        self.assertEqual(pool.inserted_values[7], 1)
        self.assertEqual([call.args[0] for call in sleep_mock.await_args_list], [0.25])

    async def test_proposed_mode_uses_fallback_after_retry_limit(self) -> None:
        pool = FakePool()
        with (
            patch("backend.app.services.chat_service.create_groq_client", return_value=object()),
            patch("backend.app.services.chat_service.maybe_simulate_primary_failure", new_callable=AsyncMock),
            patch(
                "backend.app.services.chat_service.asyncio.sleep",
                new_callable=AsyncMock,
            ) as sleep_mock,
            patch(
                "backend.app.services.chat_service._call_model",
                new_callable=AsyncMock,
                side_effect=[
                    SimulatedProviderError("rate_limit"),
                    SimulatedProviderError("rate_limit"),
                    SimulatedProviderError("rate_limit"),
                    "Fallback answer",
                ],
            ) as call_model,
        ):
            result = await execute_chat(pool, "Write a Python function.", "proposed")

        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 2)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.model, result.fallback_model)
        self.assertEqual(result.response, "Fallback answer")
        self.assertEqual(call_model.await_count, 4)
        self.assertTrue(pool.inserted_values[9])
        self.assertEqual(
            [call.args[0] for call in sleep_mock.await_args_list],
            [0.25, 0.5],
        )

    async def test_baseline_does_not_retry_or_use_fallback(self) -> None:
        pool = FakePool()
        with (
            patch("backend.app.services.chat_service.create_groq_client", return_value=object()),
            patch("backend.app.services.chat_service.maybe_simulate_primary_failure", new_callable=AsyncMock),
            patch(
                "backend.app.services.chat_service._call_model",
                new_callable=AsyncMock,
                side_effect=SimulatedProviderError("network_error"),
            ) as call_model,
        ):
            result = await execute_chat(pool, "What is a binary search?", "baseline")

        self.assertFalse(result.success)
        self.assertEqual(result.retry_count, 0)
        self.assertFalse(result.fallback_used)
        self.assertEqual(call_model.await_count, 1)


if __name__ == "__main__":
    unittest.main()
