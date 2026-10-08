"""PostgreSQL pool setup for Replit's managed PostgreSQL database."""

from __future__ import annotations

import os
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit

import asyncpg
from fastapi import Request


def _database_dsn() -> tuple[str, str | None]:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        required = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise RuntimeError(
                "PostgreSQL is not configured. Replit provides DATABASE_URL "
                "automatically; otherwise set all DB_HOST, DB_PORT, DB_USER, "
                "DB_PASSWORD, and DB_NAME values."
            )
        dsn = (
            f"postgresql://{quote_plus(os.environ['DB_USER'])}:"
            f"{quote_plus(os.environ['DB_PASSWORD'])}@"
            f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/"
            f"{quote_plus(os.environ['DB_NAME'])}"
        )

    parsed = urlsplit(dsn)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    ssl_mode = query.pop("sslmode", None)
    # asyncpg accepts TLS configuration as a connection option, not a
    # libpq-style sslmode URL parameter.
    clean_dsn = urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )
    ssl = ssl_mode if ssl_mode in {"allow", "prefer", "require", "verify-ca", "verify-full"} else None
    return clean_dsn, ssl


async def create_pool() -> asyncpg.Pool:
    dsn, ssl = _database_dsn()
    options: dict[str, object] = {
        "dsn": dsn,
        "min_size": 1,
        "max_size": 10,
        "command_timeout": 15,
    }
    if ssl:
        options["ssl"] = ssl
    try:
        return await asyncpg.create_pool(**options)
    except Exception as exc:
        raise RuntimeError("Could not connect to the configured PostgreSQL database.") from exc


async def get_pool(request: Request) -> asyncpg.Pool:
    """Provide the app's shared PostgreSQL pool to API route handlers."""
    return request.app.state.db_pool
