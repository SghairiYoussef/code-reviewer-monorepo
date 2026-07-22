# AI Code Reviewer

Automated AI-powered pull-request review. GitHub is supported first; GitLab is
kept behind the provider boundary until its inline-comment contract is complete.

## Quick Start

```bash
# Clone
git clone <repo-url>
cd code-reviewer-monorepo

# Environment (PowerShell)
Copy-Item infra/.env.example infra/.env
# Edit infra/.env with your GitHub App, OpenAI, and management API credentials

# Run
docker compose -f infra/docker-compose.yml up --build -d
```

## Development

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Tests
pytest
```

## Configuration

Set environment variables in `infra/.env` for Docker Compose, or export them in
your shell for local development:

| Variable | Description |
|----------|-------------|
| `MONGO_URI` | MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_PRIVATE_KEY` | GitHub App private key (PEM) |
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook secret |
| `GITLAB_URL` | GitLab instance URL |
| `GITLAB_TOKEN` | GitLab API token |
| `OPENAI_API_KEY` | OpenAI API key |
| `API_KEY` | Key required in `X-API-Key` for `/api/v1/*` |

## Runtime endpoints

- `POST /webhooks` — GitHub App webhook receiver (signature authenticated)
- `GET /health` — process liveness
- `GET /ready` — MongoDB and Redis readiness
- `/api/v1/*` — management/read API protected by `X-API-Key`

Repository configuration is loaded only from `.codereview.yml` at the pull
request's trusted base commit. Server-enforced database policy has final
precedence.
