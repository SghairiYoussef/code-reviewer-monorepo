# AI Code Reviewer

Automated AI-powered code review for GitHub and GitLab.

## Quick Start

```bash
# Clone
git clone <repo-url>
cd code-reviewer-monorepo

# Environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Run
docker compose up -d
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

Set environment variables in `backend/.env`:

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
