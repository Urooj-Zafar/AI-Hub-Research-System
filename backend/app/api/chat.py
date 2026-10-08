"""Chat endpoint that persists successful and failed experiment attempts."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import asyncpg

from app.database.database import get_pool
from app.models.request_model import ChatInput, ChatResult
from app.services.chat_service import execute_chat

router = APIRouter()


@router.post("/chat", response_model=ChatResult)
async def chat(
    payload: ChatInput,
    pool: asyncpg.Pool = Depends(get_pool),
) -> ChatResult | JSONResponse:
    result = await execute_chat(
        pool,
        payload.message,
        payload.experiment_mode,
    )
    if result.success:
        return result
    return JSONResponse(
        status_code=503 if result.error_type == "authentication_error" else 502,
        content=result.model_dump(mode="json", by_alias=True),
    )
