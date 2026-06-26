# QueueStorm Investigator

Evidence-grounded FastAPI service for the SUST CSE Carnival 2026 Codex Community Hackathon preliminary round.

The service exposes the required judge endpoints:

- `GET /health` returns `{"status":"ok"}`
- `POST /analyze-ticket` returns the required structured ticket analysis JSON

It also includes a small browser UI at `/`, Redis/Upstash support, rate limiting, response caching, session memory, health checks, Docker, Render config, GitHub CI, and a reproducible runbook.

## Tech Stack

- FastAPI with async endpoints
- Pydantic v2 request and response models
- Rule-based evidence investigator as the primary decision engine
- Redis or Upstash Redis for cache, session memory, and distributed rate limiting
- In-memory fallback when Redis is not configured
- Optional LLM configuration only; no LLM call is required for correctness

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- API health: `http://localhost:8000/health`
- Frontend: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

## Docker

```bash
docker build -t queuestorm-investigator .
docker run --rm -p 8000:8000 --env-file .env.example queuestorm-investigator
```

## Render Deployment

1. Push this repository to GitHub.
2. In Render, create a Blueprint from `render.yaml`.
3. Add `UPSTASH_REDIS_URL` or `REDIS_URL` as a secret environment variable if Redis is available.
4. Deploy and submit the public base URL.

The required health path is `/health`.

## Environment Variables

Copy `.env.example` to `.env` for local development.

Important variables:

- `REDIS_URL` or `UPSTASH_REDIS_URL`: optional Redis-compatible URL. Upstash Redis works here.
- `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`: request limit per client.
- `CACHE_TTL_SECONDS`: cached analysis lifetime.
- `SESSION_TTL_SECONDS`: ticket session memory lifetime.
- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`: optional metadata for future LLM use.

No secrets should be committed.

## API Contract

### `GET /health`

Returns:

```json
{"status":"ok"}
```

### `POST /analyze-ticket`

Accepts one ticket with `ticket_id`, `complaint`, optional context fields, and `transaction_history`.

Returns:

- `ticket_id`
- `relevant_transaction_id`
- `evidence_verdict`
- `case_type`
- `severity`
- `department`
- `agent_summary`
- `recommended_next_action`
- `customer_reply`
- `human_review_required`
- `confidence`
- `reason_codes`

All enum values match the problem statement exactly.

## Extra Health Checks

- `GET /health/redis` verifies Redis or reports the memory fallback.
- `GET /health/llm` reports whether optional LLM configuration is enabled.

## AI Approach

The primary analyzer is deterministic and rule-based because the rubric rewards fast, safe, schema-valid evidence reasoning. The engine:

1. Normalizes the complaint text.
2. Detects credential risk, suspicious support/social-engineering language, and prompt-injection attempts.
3. Scores transactions using amount, transaction type, counterparty, and status evidence.
4. Classifies the case into the exact allowed taxonomy.
5. Routes to the required department enum.
6. Generates a safe support summary, next action, and customer reply.

This approach avoids LLM latency, API cost, and prompt-injection risk during automated judging. Optional LLM settings are present for future manual-review summarization, but the shipped API does not depend on external AI calls.

## MODELS

- Primary model: deterministic rule engine, runs inside this FastAPI service.
- External LLM: none by default.
- Optional LLM metadata: set `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY` only if extending the service.

Cost reasoning: the default deployment has no per-request model cost and should respond well under the 30-second judge timeout.

## Safety Logic

The service never asks for PIN, OTP, password, CVV, full card number, or secret credentials. It also avoids promising refunds, reversals, account recovery, or account unblock actions. Suspicious, ambiguous, high-value, prompt-injection, and dispute cases are marked for human review.

Prompt-injection text inside the customer complaint is treated as untrusted input. It can affect safety flags, but it cannot override schema, routing, or reply rules.

## Redis, Upstash, Cache, Session Memory, Rate Limiting

Redis-compatible storage is used when `REDIS_URL` or `UPSTASH_REDIS_URL` is configured.

- Cache: repeated identical request bodies return the cached structured analysis.
- Session memory: the last analysis for each `ticket_id` is stored for operational lookup.
- Rate limiting: Redis-backed fixed-window limiting for deployed instances.
- Fallback: local in-memory cache/session/rate limiting when Redis is absent.

## Testing

```bash
pytest -q
```

The tests cover:

- Required health response
- Prompt-injection and credential-safety behavior
- Empty complaint validation

## Sample Output

See `sample_output.json` for a public sample-style input and one valid output.

## Known Limitations

- Bangla and Banglish matching is keyword-based, not a full language model.
- The rule engine is optimized for safety and schema reliability, not creative natural language.
- Redis is optional; in-memory fallback is not shared across multiple deployed replicas.
- No real payment, refund, reversal, or customer account action is performed.
