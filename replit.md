# AI Hub Research System

A university research app for comparing task-based Groq model selection and retry/fallback behavior using real PostgreSQL request data.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the Python FastAPI service behind `/api`
- `pnpm --filter @workspace/ai-hub run dev` — run the React web app
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- PostgreSQL uses Replit's managed `DATABASE_URL`
- Required secret: `GROQ_API_KEY`
- Python dependencies: `pyproject.toml` and `uv.lock`

## Stack

- React + JavaScript/JSX + Tailwind CSS frontend in `artifacts/ai-hub`
- Python + FastAPI backend in `backend/app`
- PostgreSQL + `asyncpg`; schema contract in `backend/app/database/schema.sql`
- Groq Python SDK for provider calls
- OpenAPI contract and generated API client in `lib/api-spec` and `lib/api-client-react`

## Where things live

- `artifacts/ai-hub` — React chat and research dashboard
- `backend/app/services` — task routing, error classification, retries, fallback, Groq integration
- `backend/app/database` — PostgreSQL pool and SQL schema
- `lib/api-spec/openapi.yaml` — REST API source of truth
- `README.md` — setup, operation, experiment design, and API guide

## Architecture decisions

- The API service workflow uses Python FastAPI; the old Express scaffold was removed.
- Replit's database supplies `DATABASE_URL`; separate DB_HOST/DB_* values are only a local/external fallback.
- Failure simulations are marked in PostgreSQL and excluded from the experiment metrics.
- API request history returns metadata, not the original prompt text.

## Product

- Baseline/proposed Groq chat experiments
- Rule-based task classification and deterministic model routing
- Bounded retries, exponential backoff, timeouts, and one fallback attempt
- PostgreSQL-backed research statistics and paginated attempt history

## User preferences

- Light theme only; do not add dark mode, dark backgrounds, a dark-mode toggle, or Tailwind `dark:` classes.

## Gotchas

- The API service is mounted at `/api`; FastAPI routes include that prefix because the Replit proxy does not rewrite paths.
- The Groq API key must stay in Replit Secrets and must never be exposed to React or returned by an API.
- Simulated requests are not research observations; restore simulation settings to off before collecting experiment data.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
