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

| Layer | Purpose | Status |
|-------|---------|--------|
| `vcs/` | VCS provider abstraction (webhook validation, diff fetch, comment posting) | ✅ Implemented |
| `llm/` | LLM provider abstraction (code review, summarization) | Pending |
| `services/` | Business logic — orchestrator, diff parser, config loader | Pending |
| `models/` | Beanie document models (Review, RepoConfig, Organization) | Pending |
| `schemas/` | Shared Pydantic schemas (ReviewComment) | ✅ Implemented |
| `workers/` | Celery background tasks | Pending |
| `routers/` | FastAPI API endpoints | Partial |

## VCS Abstraction Layer

The VCS layer isolates all version-control-system-specific logic behind a
single `VCSProvider` interface. The core review pipeline never imports from
`vcs/github/` or `vcs/gitlab/` directly.

### Components

- `vcs/base.py` — `VCSProvider` ABC (7 abstract methods)
- `vcs/models.py` — `VCSEnum`, `WebhookEvent`, `RepositoryInfo`
- `vcs/factory.py` — `register_provider()`, `get_provider()`, `detect_vcs_type()`
- `vcs/github/` — GitHub implementation (stub)
- `vcs/gitlab/` — GitLab implementation (stub)
- `schemas/review.py` — `ReviewComment`, `CommentSeverity`, `CommentCategory`

### Adding a New VCS Provider

1. Create `vcs/<name>/` directory
2. Implement `provider.py` with `VCSProvider` subclass
3. Implement `webhook.py` for signature validation
4. Implement `client.py` wrapping the VCS API
5. Register in `__init__.py` via `register_provider()`
6. Add to `VCSEnum` in `vcs/models.py`

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
│       │   ├── base.py          # VCSProvider ABC
│       │   ├── models.py        # VCSEnum, WebhookEvent, RepositoryInfo
│       │   ├── factory.py       # Provider registry + detection
│       │   ├── github/          # GitHub implementation (stub)
│       │   └── gitlab/          # GitLab implementation (stub)
│       ├── schemas/             # Shared Pydantic schemas
│       │   └── review.py        # ReviewComment, severity/category enums
│       ├── llm/                 # LLM provider abstraction (pending)
│       ├── models/              # Beanie document models (pending)
│       ├── services/            # Business logic (pending)
│       ├── prompts/             # LLM prompt templates (pending)
│       ├── workers/             # Celery background tasks (pending)
│       └── routers/             # FastAPI API endpoints
│           ├── webhooks.py      # POST /webhooks — implemented
│           ├── reviews.py       # GET /reviews — stub
│           └── repos.py         # CRUD /repos — stub
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   └── DECISIONS.md
└── frontend/                    # Empty — dashboard in future phase
```

## Config Precedence

`.codereview.yml` in repo → DB config → app defaults
