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
| `vcs/` | VCS contract and GitHub implementation; GitLab is deliberately unregistered | GitHub implemented |
| `llm/` | Bounded structured OpenAI review | Implemented |
| `services/` | Ingestion, trusted config merge, diff-coordinate validation | Implemented |
| `models/` | Beanie Review and RepositoryConfig documents | Implemented |
| `schemas/` | Shared Pydantic schemas (ReviewComment) | ✅ Implemented |
| `workers/` | Idempotent Celery review task | Implemented |
| `routers/` | Webhook and API-key-protected management endpoints | Implemented |

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

## Config and Trust Precedence

Server-enforced DB policy → `.codereview.yml` from the PR **base commit** → app
defaults. Repository files can only set bounded review fields; credentials,
provider/model selection, and service limits are never read from PR content.

## Runtime Boundaries

- FastAPI validates signatures, persists an idempotency record, and dispatches work.
- Celery workers use synchronous VCS/LLM clients; asynchronous code is limited to
  Beanie persistence within one task-owned event loop.
- `GET /health` is liveness-only; `GET /ready` verifies MongoDB and Redis.
- Management endpoints require `X-API-Key`. Webhooks use provider signatures.
