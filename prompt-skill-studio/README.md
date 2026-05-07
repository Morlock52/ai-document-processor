# Prompt & Skill Studio

A dark-first IDE-style GUI for designing and testing **prompts**, **Anthropic Skills**, **OpenAI Agents SDK** specs, and **MCP server stubs** against the latest OpenAI and Anthropic models — with a built-in doc-sync subsystem that keeps the model catalog and prompt-engineering guidance fresh.

## Why this exists

Vendor guidance moves fast. New models, new beta headers, deprecated APIs (Assistants API sunsets 2026-08-26), new SKILL.md fields. This studio polls each vendor's machine-readable doc surfaces (`llms.txt`, changelog RSS) on a schedule and surfaces "what changed" so the prompts and skills you author are always grounded in current best practice.

## Architecture

Five Railway services + managed Postgres + managed Redis:

| Service  | Stack                          | Purpose                                  |
| -------- | ------------------------------ | ---------------------------------------- |
| `web`    | Next.js 15, shadcn/ui, Monaco  | The GUI                                  |
| `api`    | FastAPI, SQLAlchemy            | REST + SSE streaming for runs            |
| `worker` | RQ                             | Background jobs (doc sync, exports)      |
| `cron`   | Single-shot job                | Enqueues `sync_vendor_docs` every 6h     |
| db       | Postgres 15                    | Catalog, artifacts, runs, encrypted keys |
| redis    | Redis 7                        | Queue + SSE backplane                    |

Local dev mirrors the same five services via `docker-compose.yml`.

## Quick start (local)

```bash
cp .env.example .env
# Edit .env: set STUDIO_PASSCODE, STUDIO_MASTER_KEY (32-byte base64).
docker-compose up --build
# web:    http://localhost:3000
# api:    http://localhost:8000/docs
```

Generate a master key:

```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

## Deploy to Railway

1. `railway link` your project, then `railway up`.
2. Add Postgres and Redis plugins; Railway will inject `DATABASE_URL` and `REDIS_URL`.
3. Set env vars on the **api**, **worker**, and **cron** services: `STUDIO_PASSCODE`, `STUDIO_MASTER_KEY`.
4. Set `NEXT_PUBLIC_API_URL` on the **web** service to the public URL of the **api** service.
5. The `cron` service runs `python -m app.jobs.cron_enqueue` on a 6h schedule.

See `railway.json` for the service definitions.

## Vendor coverage

| Vendor    | Models tracked (May 2026)                                                  | Doc sources polled                                     |
| --------- | -------------------------------------------------------------------------- | ------------------------------------------------------ |
| Anthropic | Opus 4.7, Sonnet 4.6, Haiku 4.5 (+ legacy Opus 4.6 / 4.1)                  | docs.anthropic.com/llms.txt, code.claude.com/docs/llms.txt, /release-notes/overview |
| OpenAI    | GPT-5.5 / 5.5 Pro / 5.5 Instant, o3, o3-pro, o4-mini                       | platform.openai.com/docs/llms.txt, developers.openai.com/api/llms-full.txt, /changelog/ RSS |

If a vendor URL returns 403/429/5xx, the existing catalog stays serving and a "stale since …" banner appears.

## Bring-your-own-key

Vendor keys are stored AES-256-GCM encrypted with `STUDIO_MASTER_KEY`. They are decrypted only inside a request scope, passed to the SDK, and never logged. See `backend/app/core/crypto.py`.

## Repo layout

```
prompt-skill-studio/
├── docker-compose.yml
├── railway.json
├── .env.example
├── frontend/   # Next.js 15
└── backend/    # FastAPI + RQ worker
```

## Status

This is M1 (catalog + prompt CRUD). M2 adds the playground; M3 adds Agents + MCP authoring; M4 adds the change feed. See `/root/.claude/plans/could-you-help-me-smooth-spark.md` for the full plan.
