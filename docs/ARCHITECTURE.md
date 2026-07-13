# Architecture

## Stack

- **Backend**: FastAPI + Beanie (MongoDB ODM)
- **Queue**: Celery + Redis
- **VCS**: Abstract provider layer → GitHub + GitLab
- **LLM**: Abstract provider layer → OpenAI GPT-4o

## Flow

```
VCS webhook → FastAPI → validate → create Review (DB) → dispatch Celery task → 202
Celery worker: fetch diff → chunk → LLM review → parse response → post comments
```

## Key Layers

| Layer | Purpose |
|-------|---------|
| `vcs/` | VCS provider abstraction (webhook validation, diff fetch, comment posting) |
| `llm/` | LLM provider abstraction (code review, summarization) |
| `services/` | Business logic — orchestrator, diff parser, config loader |
| `models/` | Beanie document models (Review, RepoConfig, Organization) |
| `workers/` | Celery background tasks |
| `routers/` | FastAPI API endpoints |

## Project Structure

```
├── infra/
│   ├── docker-compose.yml       # Mongo + Redis + backend + celery-worker
│   └── .env.example             # Template for env vars
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py              # FastAPI app, lifespan, CORS, router mounts
│       ├── config.py            # Pydantic Settings (env-based config)
│       ├── deps.py              # Dependency injection
│       ├── vcs/                 # VCS provider abstraction
│       ├── llm/                 # LLM provider abstraction
│       ├── models/              # Beanie document models
│       ├── schemas/             # Pydantic request/response schemas
│       ├── services/            # Business logic
│       ├── prompts/             # LLM prompt templates
│       ├── workers/             # Celery background tasks
│       └── routers/             # FastAPI API endpoints
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   └── DECISIONS.md
└── frontend/                    # Empty — dashboard in future phase
```

## Config Precedence

`.codereview.yml` in repo → DB config → app defaults
