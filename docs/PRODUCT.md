# AI Code Reviewer

Automated code review tool that integrates with GitHub and GitLab via webhooks,
using AI language models to post inline review comments on pull/merge requests.

## Goal

Augment code review workflows with AI-powered feedback — catch bugs, security
issues, and style problems before human reviewers spend time on the first pass.

## MVP Scope

- Webhook-driven: push → analyze → comment
- GitHub (PRs) + GitLab (MRs) support
- Provider-agnostic LLM layer (OpenAI GPT-4o first)
- Multi-language code review
- Inline comments + PR/MR summary per review
- Configurable review rules per repo

## Non-Goals (MVP)

- Web dashboard
- CI/CD pipeline gates
- Code generation or fix suggestions
- Authentication/authorization
