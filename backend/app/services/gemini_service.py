"""Gemini API integration for cross-provider fallback."""

from __future__ import annotations

import os

from google import genai
from google.genai import types


async def call_gemini(model_id: str, message: str) -> str:
    """Generate a response using the configured Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    async with genai.Client(api_key=api_key).aio as client:
        result = await client.models.generate_content(
            model=model_id,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Answer clearly and accurately. "
                    "If a request is ambiguous, state the assumption you use."
                ),
                max_output_tokens=2048,
            ),
        )

    response = result.text

    if not response:
        raise RuntimeError("Gemini returned an empty response.")

    return response