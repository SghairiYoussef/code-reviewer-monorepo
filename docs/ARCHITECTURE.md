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

## Config Precedence

`.codereview.yml` in repo → DB config → app defaults
