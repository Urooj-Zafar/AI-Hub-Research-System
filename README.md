# AI Hub Research System

AI Hub is a university research project for comparing a fixed-model baseline
with a task-aware AI system that uses bounded retries, exponential backoff,
timeouts, and a fallback model. It uses real Groq responses and stores each
attempt in PostgreSQL. Dashboard metrics are calculated from those stored
records; no example research results are seeded.

## Research objective

The project studies whether task classification and resilience techniques
affect the reliability and response time of an AI request system. It provides
the tools to collect and compare data, but it does not declare either system
better. Run experiments and interpret the real results yourself.

## Research problem

A single-model chatbot can fail because of a timeout, rate limit, network
problem, or provider error. AI Hub tests whether choosing a model by task and
recovering from retryable errors improves the observed results compared with
using one fixed model.

## Technology

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **API:** REST over HTTP, JSON request and response bodies
- **Frontend:** React, JavaScript/JSX, Tailwind CSS
- **Database:** Replit-managed PostgreSQL, accessed with `asyncpg`
- **AI:** Groq API using the official Groq Python SDK
- **Development:** Replit workflows

The backend is FastAPI, not Express. The React app never calls Groq directly;
the request path is React → FastAPI → Groq.

## Architecture

```text
Browser (React + Tailwind)
        │ HTTP + JSON
        ▼
FastAPI REST API (/api)
        │
        ├── Rule-based task classifier
        ├── Baseline or deterministic task-based model selector
        ├── Groq API, bounded retries, timeout and optional fallback
        └── PostgreSQL request logging and aggregate queries
                   │
                   ▼
           Research dashboard
```

The UI is light-theme only. It has no dark-mode toggle or dark theme.

## API

The API is served under `/api`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/` | App name, description, and version |
| `GET` | `/api/health` | Health check; returns `{"status":"ok"}` |
| `GET` | `/api/healthz` | Replit service liveness check |
| `POST` | `/api/chat` | Run and record a baseline or proposed experiment |
| `GET` | `/api/statistics` | PostgreSQL-backed aggregates |
| `GET` | `/api/requests` | Paginated request metadata; supports `limit`, `offset`, and `experimentMode` |
| `GET` | `/api/docs` | FastAPI interactive API documentation |

Example chat request:

```json
{
  "message": "Write a JavaScript function for binary search.",
  "experimentMode": "proposed"
}
```

`experimentMode` must be `baseline` or `proposed`. A completed attempt returns
its success state, response or safe error message, detected task, selected
model, response time, retry count, fallback state, and simulation flag. A
provider failure is also stored before the API returns an error response.

The request-history endpoint returns model and performance metadata, not the
original prompt text. Prompts are still stored in PostgreSQL for the research
owner. Do not enter personal, confidential, or secret data: this project has no
user authentication, and prompt records are accessible to the project owner.

## Task classification

`backend/app/services/model_selector.py` uses readable keyword patterns in
this order:

1. Coding terms such as `function`, `debug`, `Python`, and `SQL`
2. Creative terms such as `story`, `poem`, `fiction`, and `dialogue`
3. Reasoning terms such as `solve`, `prove`, `compare`, and `step by step`
4. Anything not matched defaults to **General Knowledge**

This is deliberately a simple, explainable classifier, not a machine-learning
model. If a query contains signals from more than one group, the first matching
group wins.

## Baseline and proposed experiments

- **Baseline:** every query uses one fixed Groq model. It does not select by
  task, retry, or switch to a fallback model. The request is still bounded by
  the configured timeout.
- **Proposed:** selects a configured model deterministically from the task
  type; retries retryable errors up to `MAX_RETRIES`; waits
  `RETRY_BASE_DELAY_SECONDS × 2^retry_count` before a retry; and tries the
  configured fallback once after the primary path fails.

The error classifier recognizes `timeout`, `rate_limit`, `server_error`,
`network_error`, `authentication_error`, `invalid_request`, and `unknown_error`.
Only timeout, rate-limit, server, and network errors are retried. The Groq SDK's
own retry feature is disabled so retry counts and backoff measurements describe
the research mechanism, not hidden SDK retries.

## Groq and model configuration

Set `GROQ_API_KEY` with Replit Secrets. Never place it in source code, a prompt,
or a frontend variable. The backend checks configured model IDs against Groq's
active model list before use. The initial choices are defined together in
`backend/app/core/config.py`; change them there or use the documented
`GROQ_MODEL_*`, `GROQ_BASELINE_MODEL`, and `GROQ_FALLBACK_MODEL` overrides.
The current account's active model list was checked during setup; the selected
IDs are `qwen/qwen3.8-27b`, `openai/gpt-oss-20b`, and
`openai/gpt-oss-120b`. The app checks active IDs again before use. Update the
model choices if Groq changes its active model list.

The API key was intentionally not checked into `.env.example`.

## PostgreSQL and recorded data

The only database is PostgreSQL. Replit supplies `DATABASE_URL` to the backend.
When running outside Replit, configure `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, and `DB_NAME` instead.

The `ai_requests` table records:

- ID, user query, task type, and baseline/proposed experiment mode
- Primary, fallback, and final model IDs
- Actual elapsed response time in milliseconds and retry count
- Classified error, fallback use, final status, and timestamp
- Whether the attempt involved controlled failure simulation

`backend/app/database/schema.sql` documents the schema. The development
PostgreSQL schema was applied to this project. The backend opens a connection
pool at startup and does not create tables during application startup.

Statistics are aggregated from actual rows in PostgreSQL. Simulated attempts
are reported as an excluded count, but are left out of the success/failure
rates, timing, retries, model usage, task distribution, error analysis, and
baseline/proposed comparison. Empty datasets show zero counts; they are not
sample measurements.

## React frontend

`artifacts/ai-hub` contains the React and JSX application. It communicates with
FastAPI through the generated REST client in `@workspace/api-client-react`.
The chat page sends real requests and displays the returned system details.
The dashboard loads actual statistics and paginated request metadata from the
API. There is no hardcoded sample chat, fake metrics, or dark-mode code.

## Failure simulation

Simulation is off by default:

```text
SIMULATE_FAILURE=false
FAILURE_RATE=0
```

To test the retry path and fallback on Replit, set these values in the API
service environment:

```text
SIMULATE_FAILURE=true
FAILURE_RATE=1
```

The simulation injects marked primary-model errors and lets the fallback make
a real Groq call. For baseline requests, the simulated primary failure ends the
attempt without retry or fallback. Simulated attempts remain identifiable in
the request list and are excluded from research metrics. Restore `false` and
`0` before collecting experiment data; simulated attempts are not evidence of
real provider performance.

## Environment variables

| Name | Purpose | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Groq credential; configure only in Replit Secrets | Required for chat |
| `DATABASE_URL` | Replit-managed PostgreSQL connection | Supplied by Replit |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Alternative PostgreSQL connection details | Not used when `DATABASE_URL` exists |
| `GROQ_MODEL_CODING` | Proposed model for Coding | `qwen/qwen3.8-27b` |
| `GROQ_MODEL_GENERAL` | Proposed model for General Knowledge | `openai/gpt-oss-20b` |
| `GROQ_MODEL_REASONING` | Proposed model for Reasoning | `openai/gpt-oss-120b` |
| `GROQ_MODEL_CREATIVE` | Proposed model for Creative Writing | `qwen/qwen3.8-27b` |
| `GROQ_BASELINE_MODEL` | Fixed model for baseline runs | `openai/gpt-oss-20b` |
| `GROQ_FALLBACK_MODEL` | Single proposed-system fallback | `openai/gpt-oss-20b` |
| `GROQ_TIMEOUT_SECONDS` | Maximum time for each Groq call | `20` |
| `MAX_RETRIES` | Proposed-system retry limit | `2` |
| `RETRY_BASE_DELAY_SECONDS` | First exponential-backoff delay | `0.25` |
| `SIMULATE_FAILURE` | Enable controlled test errors | `false` |
| `FAILURE_RATE` | Probability of a test error per primary attempt, from 0 to 1 | `0` |
| `CORS_ORIGINS` | Comma-separated development origins | Local Vite origins |

Replit-managed `DATABASE_URL` and PostgreSQL variables should not be added
manually. The full example is in `backend/.env.example`.

## Run in Replit

The project has two managed workflows:

- **AI Hub web:** starts the React/Vite frontend.
- **API Server:** runs `python -m uvicorn backend.app.main:app` through the
  shared `/api` service route.

Use Replit's Run control to start both. For manual development:

```bash
pnpm --filter @workspace/ai-hub run dev
pnpm --filter @workspace/api-server run dev
```

Python dependencies are tracked by the root `pyproject.toml` and `uv.lock`.
Outside Replit, run `uv sync` from the project root, or install the
`backend/requirements.txt` packages with pip. The API server must be able to
read `GROQ_API_KEY` and the Replit PostgreSQL environment.

Open the root app preview to use AI Hub. Open the dashboard from the app's
navigation.

## How to use the system

1. Pick **Baseline** or **Proposed** on the chat page.
2. Enter a non-sensitive research query and submit it.
3. Read the generated response and the returned task/model/time/retry/fallback
   information.
4. Use the Dashboard to review actual PostgreSQL records and aggregates.
5. Keep the simulation off while collecting final experiment data.

## How to test the REST API

The API is available under `/api` in the Replit preview:

```bash
curl "$REPLIT_DEV_DOMAIN/api/health"
curl "$REPLIT_DEV_DOMAIN/api/statistics"
curl "$REPLIT_DEV_DOMAIN/api/requests?limit=10&offset=0"
curl -X POST "$REPLIT_DEV_DOMAIN/api/chat" \
  -H 'Content-Type: application/json' \
  -d '{"message":"If A is greater than B and B is greater than C, which is greatest?","experimentMode":"proposed"}'
```

In the interactive API page, use `/api/docs`. A valid chat request is sent
through FastAPI to Groq and recorded in PostgreSQL. Empty messages are rejected
by request validation.

## Backend unit checks

Run the backend checks without calling Groq or inserting test records into
PostgreSQL:

```bash
python -m unittest discover -s backend/tests
python -m compileall -q backend
```

These checks cover the four example task classifications, fixed/deterministic
model selection, retry limits, backoff path, fallback behavior, and error
classification. Actual provider and database availability are checked
separately by the running API and its health/statistics endpoints.

## Important research cautions

- Do not interpret empty-dataset zeroes as evidence.
- Do not treat controlled simulation records as real API outcomes.
- No statistical significance tests or conclusions are generated.
- Run enough baseline and proposed trials under comparable conditions before
  making claims about reliability or performance.
- Because this first version has no accounts, anyone with access to the app
  can submit queries and view aggregate/request metadata. Keep queries
  non-sensitive.
