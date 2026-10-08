"""FastAPI app entry point. All REST paths include the shared /api prefix."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.chat import router as chat_router
from backend.app.api.health import router as health_router
from backend.app.api.statistics import router as statistics_router
from backend.app.database.database import create_pool

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("ai_hub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool: asyncpg.Pool | None = None
    try:
        pool = await create_pool()
        await pool.fetchval("SELECT 1")
        app.state.db_pool = pool
        logger.info("PostgreSQL connection pool is ready.")
        yield
    except Exception:
        logger.exception("FastAPI could not start with the configured PostgreSQL database.")
        raise
    finally:
        if pool is not None:
            await pool.close()


app = FastAPI(
    title="AI Hub Research System API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "AI Hub Research System API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
