# Cashlibot

Telegram personal finance tracker: bot + Mini App + admin dashboard.

This repository is in early-build. See `master-prompt.md` (or the original spec) for the full design.

## Stack at a glance

| Layer | Tech |
|---|---|
| Bot | aiogram 3 |
| API | FastAPI |
| Worker | APScheduler 4 (co-located with bot for now) |
| DB | PostgreSQL 16 + pgvector |
| ORM | SQLModel (SQLAlchemy 2 + Pydantic) |
| Cache / queues | Redis 7 |
| AI orchestration | LangChain (provider-agnostic) |
| Mini App | React 18 + Vite + TS |
| Admin | React 18 + Vite + TS |

## Running locally

You need:

- Docker Desktop running
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))
- Optionally, an AI provider API key (DeepSeek / OpenAI / Anthropic) — only required once AI features are wired in

### First time

```bash
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN at minimum
docker compose up --build
```

That brings up:

| Service | URL / Port |
|---|---|
| Postgres (pgvector) | `localhost:5432` |
| Redis | `localhost:6379` |
| API (FastAPI) | `http://localhost:8000` — try `/health` |
| Bot | polling Telegram (no exposed port) |
| Mini App (Vite dev) | `http://localhost:5173` |
| Admin (Vite dev) | `http://localhost:5174` |

Migrations run automatically on api / bot startup.

### Stop everything

```bash
docker compose down
```

### Reset the database

```bash
docker compose down -v
```

`-v` removes the named postgres volume, so the next `up` re-runs all migrations against a clean DB.

## Repository layout

```
backend/   FastAPI app + aiogram bot + APScheduler worker (one Python project)
miniapp/   React + Vite Telegram Mini App
admin/     React + Vite admin dashboard
nginx/     Reverse proxy config (used in prod deploys, not local dev)
```

## Workflow

- Trunk-based: `master` is always deployable.
- All work on short-lived feature branches: `feat/<scope>/<description>`.
- Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `chore`).
- Every branch merged via Pull Request.
- No CI/CD wiring yet — deployment is manual `docker compose up` on a server.

## What's built

This is the first scaffold commit. Working today:

- Docker Compose brings everything up cleanly
- YAML configs (`currencies.yaml`, `ai_providers.yaml`, `app.yaml`) load + validate on startup
- Postgres has the `vector` extension enabled
- Alembic migration creates the `user` table
- FastAPI `/health` returns OK
- Bot responds to `/start` with a stubbed welcome
- Both frontends boot to a placeholder page

Everything else from the spec — accounts, transactions, AI agent, mini app screens, admin dashboard, friends, gamification, etc. — is upcoming work.
