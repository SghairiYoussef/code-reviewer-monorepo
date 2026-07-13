# Architecture Decision Records — AI Code Reviewer

Each decision follows the ADR format: **Context → Alternatives Considered → Decision → Consequences**.

---

## ADR-001: Python (FastAPI) as Backend Stack

**Status**: Accepted

### Context

The backend needs to handle incoming webhooks, orchestrate LLM calls, interact
with VCS APIs, and serve a REST API for querying review results. Key
requirements: async I/O (webhook handling, external API calls), fast development
velocity, strong AI/ML ecosystem.

### Alternatives Considered

1. **TypeScript (NestJS / Express)** — Strong typing, good async model, large ecosystem.
   - Rejected because: Weaker AI/ML ecosystem. OpenAI and most LLM SDKs have
     first-class Python support. Would need to wrap Python LLM calls or use
     HTTP clients, adding latency and complexity.

2. **Go** — Excellent performance, strong concurrency model.
   - Rejected because: Verbose for rapid prototyping. Smaller ecosystem for
     AI/ML integration. Overkill for a webhook-driven service where Python's
     async model is sufficient.

3. **Python (Django / DRF)** — Mature, batteries-included.
   - Rejected because: Synchronous by default, async support still bolted-on.
     Heavier opinionated structure that fights against lightweight webhook
     handlers. FastAPI's Pydantic integration is a better fit for schema-heavy
     webhook/API work.

### Decision

**Python with FastAPI**. Async-native, Pydantic for request/response validation,
OpenAPI docs generated automatically, lightweight enough for webhook endpoints
and background task dispatch.

### Consequences

- (+) First-class LLM SDK support (OpenAI, Anthropic Python libraries)
- (+) Pydantic integration for request validation and config management
- (+) Automatic OpenAPI/Swagger docs
- (+) Large talent pool, easy onboarding
- (-) Slower than Go for CPU-bound work (acceptable — review pipeline is I/O-bound)
- (-) GIL limits true parallelism (mitigated by Celery workers)

---

## ADR-002: Monorepo with `backend/` + `frontend/`

**Status**: Accepted

### Context

The project will eventually include both a backend API service and a web
dashboard frontend. Initial implementation is backend-only, but the structure
should accommodate the frontend without major reorganization.

### Alternatives Considered

1. **Separate repositories** — Independent repos for backend and frontend.
   - Rejected because: Harder to coordinate API contract changes during early
     development. Two git histories to manage. Documentation split across repos.
   - Would work for: Mature projects with stable, versioned APIs.

2. **Single FastAPI app serving both API and frontend** — Serve React/Next.js
   static assets from FastAPI.
   - Rejected because: Different deployment cycles, different scaling needs,
     different developer workflows. Mixing concerns makes both harder to develop
     and deploy independently.

### Decision

Monorepo with top-level `backend/` and `frontend/` directories. Each is an
independent project with its own dependency management. Shared `docs/` directory
holds cross-cutting documentation.

### Consequences

- (+) Easy to add `frontend/` when dashboard phase begins
- (+) Single git history for all project documentation
- (+) Shared CI/CD pipeline possible
- (-) Backend and frontend coupling through docs only (acceptable)
- (-) Need to keep dependency trees separate (no accidental imports)

---

## ADR-003: MongoDB + Beanie ODM

**Status**: Accepted

### Context

The system needs to store review results, repository configurations, and
organization data. The data model is document-oriented (reviews contain
embedded comment arrays, configs have nested rules). High read/write throughput
for webhook processing.

### Alternatives Considered

1. **PostgreSQL + SQLAlchemy** — Industry-standard relational DB, strong
   consistency, ACID transactions.
   - Rejected because: Review data is naturally document-shaped (embedded
     comments, flexible schema per review). SQL joins unnecessary for our
     access patterns. Schema migrations add overhead for a project that will
     evolve rapidly.

2. **MongoDB + raw Motor driver** — Direct async MongoDB driver, no ODM.
   - Rejected because: No Pydantic validation on stored documents. Manual
     serialization/deserialization. More boilerplate for queries. Loses the
     benefit of Pydantic models that FastAPI already uses for request/response.

3. **MongoDB + MongoEngine** — Mature ODM, but sync-first.
   - Rejected because: Not async-native. Would need to run MongoEngine calls
     in thread executors with FastAPI, defeating the purpose of async. Beanie
     is built on Motor (async) and integrates with Pydantic v2 natively.

4. **SQLite + SQLAlchemy** — Simple, no external DB needed for MVP.
   - Rejected because: No concurrent write support. Not suitable for cloud
     deployment. Would need migration to PostgreSQL/MongoDB later anyway.

### Decision

**MongoDB with Beanie ODM**. Beanie is async-native (built on Motor), uses
Pydantic v2 models as document schemas, and integrates seamlessly with FastAPI's
async request handling.

### Consequences

- (+) Async-native, no thread executor hacks
- (+) Pydantic v2 models for both API and storage (single source of truth)
- (+) Flexible schema for evolving review/comment structures
- (+) Good horizontal scalability for cloud deployment
- (-) No multi-document transactions needed (acceptable for our use case)
- (-) Eventual consistency on some operations (acceptable — reviews are append-mostly)
- (-) Beanie is younger than SQLAlchemy (acceptable — it's stable and well-maintained)

---

## ADR-004: Celery + Redis for Task Queue

**Status**: Accepted

### Context

Webhook processing must not block the HTTP response. Reviews involve multiple
external API calls (fetch diff, call LLM, post comments) that can take 30s-2min.
The system needs reliable background processing with retry logic and monitoring.

### Alternatives Considered

1. **FastAPI BackgroundTasks only** — Use FastAPI's built-in background task
   mechanism.
   - Rejected because: No retry logic, no monitoring, no rate limiting, no
     visibility into task state. Tasks die with the process. No distributed
     processing. Suitable for trivial fire-and-forget tasks, not for a
     review pipeline that needs reliability.

2. **ARQ (async Redis queue)** — Lightweight async task queue built on Redis.
   - Rejected because: Less mature than Celery. Smaller ecosystem, fewer
     monitoring tools (no Flower equivalent). No built-in result backend.
     Would work for simple cases but limits future extensibility.

3. **Temporal** — Durable workflow engine.
   - Rejected because: Heavyweight for MVP. Requires separate server deployment.
     Overkill for a linear pipeline (fetch → review → post). Good for complex
     multi-step workflows with human approval steps — not needed yet.

4. **RQ (Redis Queue)** — Simple Python queue backed by Redis.
   - Rejected because: Synchronous worker model. Less mature than Celery.
     No built-in support for async task execution.

### Decision

**Celery with Redis as broker and backend**. Celery is the de facto standard
for Python background tasks. Redis provides fast message passing and result
storage. Celery's retry mechanisms, rate limiting, monitoring (Flower), and
task chaining (chord/group) support the review pipeline's needs.

### Consequences

- (+) Battle-tested, extensive documentation and community
- (+) Built-in retry with exponential backoff
- (+) Task result tracking via Redis backend
- (+) Flower for monitoring task queues in production
- (+) chord/group for parallel per-file review chunks
- (-) Redis as single point of failure (mitigated by Redis Sentinel/Cluster in production)
- (-) Celery configuration can be complex (mitigated by keeping task graph simple)

---

## ADR-005: VCS Provider Abstraction Layer

**Status**: Accepted

### Context

The tool needs to support multiple VCS providers (GitHub, GitLab, and potentially
Azure DevOps, Gitea in the future). Each provider has different:
- Webhook formats and signature validation (HMAC-SHA256 vs secret token vs IP whitelist)
- API endpoints for fetching diffs and posting comments
- Event naming conventions (pull_request vs merge_request)
- Authentication models (GitHub App tokens vs GitLab personal/project tokens)

Without abstraction, VCS-specific logic would leak into the review pipeline,
making it impossible to add new providers without modifying business logic.

### Alternatives Considered

1. **No abstraction, GitHub-only initially** — Build GitHub support first,
   abstract later when GitLab is needed.
   - Rejected because: Retrofitting abstraction onto existing code is harder
     than building it from the start. VCS-specific code (header parsing,
     API calls, comment formatting) would be scattered across routers,
     services, and workers. Refactoring later creates merge conflicts and
     risks breaking working code.

2. **Strategy pattern with duck typing (no ABC)** — Use Python Protocols
   instead of abstract base classes.
   - Rejected because: Protocols are structural (implicit interface). ABCs
     provide explicit contracts with clear error messages at instantiation
     time. For a multi-developer project, an explicit ABC makes the interface
     discoverable and self-documenting.

3. **Separate microservices per VCS** — Each VCS provider is a separate
   service communicating via message queue.
   - Rejected because: Massive over-engineering for MVP. Deployment complexity
     explodes. Shared logic (diff parsing, review orchestration) would need
     to be duplicated or extracted into yet another service.

### Decision

**Abstract `VCSProvider` base class** in `app/vcs/base.py`. Each provider
(GitLab, GitHub) implements this interface in its own subdirectory. A factory
in `app/vcs/factory.py` selects the provider based on the `vcs_type` string
stored in `RepoConfig`.

The core review pipeline (`review_orchestrator.py`) depends only on the
`VCSProvider` interface — never on concrete implementations.

### Consequences

- (+) Adding a new VCS requires only: implement ABC, register in factory
- (+) Core pipeline is testable with mock VCS providers
- (+) VCS-specific code is isolated and maintainable
- (-) Extra abstraction layer (acceptable — justified by multi-VCS requirement)
- (-) All providers must conform to the same interface (some VCS features may
  not map cleanly — handled by raising `NotImplementedError` for unsupported
  operations)

---

## ADR-006: LLM Provider Abstraction Layer

**Status**: Accepted

### Context

Different LLM providers have different APIs, pricing, rate limits, and
capabilities. The system should support switching providers per repository
without code changes. Future need for self-hosted/local models.

### Alternatives Considered

1. **Hardcode OpenAI SDK** — Use OpenAI directly, switch later if needed.
   - Rejected because: Same retrofitting problem as VCS abstraction. LLM calls
     are spread across review and summarization logic. Swapping later means
     touching every call site.

2. **LangChain** — Use LangChain's LLM abstraction.
   - Rejected because: Heavy dependency, opinionated abstractions that may not
     fit our use case. Adds complexity for what is essentially a single API
     call per provider. We don't need chain orchestration, memory, or agents.

3. **LiteLLM** — Unified interface for 100+ LLM providers.
   - Rejected because: Adds a dependency we don't fully control. May abstract
     too much — we need fine-grained control over retry logic, rate limiting,
     and response parsing per provider. Worth revisiting if provider count
     grows beyond 3-4.

### Decision

**Abstract `LLMProvider` base class** in `app/llm/base.py`. Each provider
implements `review_chunks()` and `summarize()` methods. Factory in
`app/llm/factory.py` selects provider from `RepoConfig.llm_provider`.

### Consequences

- (+) Per-repo provider selection via config
- (+) Easy to add Anthropic, self-hosted models later
- (+) Testable with mock LLM responses
- (-) Need to handle rate limits and retries per-provider (acceptable — each
  provider has different limits anyway)
- (-) Response parsing differs per provider (acceptable — isolated in each
  provider's implementation)

---

## ADR-007: Single Webhook Endpoint with Auto-Detection

**Status**: Accepted

### Context

Each VCS provider sends webhooks to different URL paths by convention
(`/webhooks/github`, `/api/v1/projects/:id/hooks` for GitLab). The system
needs to receive webhooks from all supported providers.

### Alternatives Considered

1. **Separate routes per VCS** — `/webhooks/github`, `/webhooks/gitlab`,
   `/webhooks/gitea`, etc.
   - Rejected because: Route explosion as providers are added. Each new VCS
     requires a new route definition. The validation and parsing logic is
     already provider-specific (inside the VCS layer), so separate routes
     add no value.

2. **Single endpoint with query param** — `/webhooks?vcs=github`.
   - Rejected because: Query params can be tampered with. Less RESTful.
     Doesn't match how VCS platforms actually send webhooks (they hit a
     single URL with headers).

3. **Path-based with VCS in URL** — `/webhooks/:vcs_type`.
   - Rejected because: Nearly identical to option 1. Same route explosion.
     Slightly cleaner but no real advantage over auto-detection.

### Decision

**Single `POST /webhooks` endpoint** that auto-detects the VCS provider from
request headers:
- `x-github-event` present → GitHub
- `x-gitlab-event` present → GitLab

The detected provider string is used to load the correct `VCSProvider` from
the factory.

### Consequences

- (+) One route to maintain, regardless of provider count
- (+) Matches how VCS platforms actually send webhooks
- (+) Adding a new VCS is just: detect header → register in factory
- (-) Header detection is heuristic (acceptable — headers are well-defined per VCS)
- (-) No way to disable a specific VCS at the route level (handled by provider
  config instead)

---

## ADR-008: OpenAI GPT-4o as First LLM Provider

**Status**: Accepted

### Context

Need to pick one LLM provider for initial implementation. Provider must be
widely available, have strong code understanding, and offer structured output.

### Alternatives Considered

1. **Anthropic Claude 3.5 Sonnet** — Excellent at code review, larger context
   window.
   - Not rejected — planned for Phase 2. OpenAI chosen first because of
     broader community adoption and more mature Python SDK.

2. **Self-hosted open-source model (Llama, CodeLlama)** — No API costs,
   full control.
   - Rejected for MVP because: Requires model serving infrastructure (GPU
     instances, inference servers). Adds significant operational complexity.
     Quality may not match commercial models for code review tasks.

3. **Azure OpenAI** — Same models, Azure infrastructure.
   - Not rejected — can be swapped in via config if deployment is on Azure.
     OpenAI API chosen for simplicity in MVP.

### Decision

**OpenAI GPT-4o** via the official Python `openai` SDK. Provider implementation
in `app/llm/openai_provider.py`. Structured JSON output for review comments.

### Consequences

- (+) Widest adoption, extensive documentation and examples
- (+) Strong code understanding capabilities
- (+) Structured output (JSON mode) for reliable parsing
- (+) Easy to swap to Azure OpenAI later (same API)
- (-) API costs scale with review volume (acceptable — can add caching later)
- (-) Rate limits on free/tier accounts (acceptable — handled by retry logic)

---

## ADR-009: GitHub First, Then GitLab

**Status**: Accepted

### Context

Both GitHub and GitLab are in MVP scope. Need to decide implementation order.

### Alternatives Considered

1. **GitLab first** — Start with GitLab as a design exercise.
   - Rejected because: GitHub has larger market share, more community examples,
     better documentation for webhook/App integration. More developers will
     try the tool on GitHub first.

2. **Both simultaneously** — Build both abstractions in parallel.
   - Rejected because: Can't validate the abstraction layer with two
     implementations at once. Need one working end-to-end flow first to
     identify interface gaps before building the second implementation.

### Decision

**GitHub first**, then GitLab. GitHub's webhook and PR comment APIs are
well-documented and widely used. Implementing GitHub first validates the
`VCSProvider` interface. GitLab implementation follows once the interface
is proven.

### Consequences

- (+) Faster time to first working review
- (+) Interface validated against real-world usage before GitLab implementation
- (+) GitHub's larger community provides more test cases
- (-) GitLab-specific features (e.g., MR approval rules) delayed to Phase 2

---

## ADR-010: In-Repo `.codereview.yml` Overrides DB Config

**Status**: Accepted

### Context

Review rules need to be configurable per repository. Two sources of config
exist: database-stored `RepoConfig` (managed via API) and a `.codereview.yml`
file that developers commit to their repo.

### Alternatives Considered

1. **DB config only** — All configuration managed via API, no in-repo file.
   - Rejected because: Developers can't see or version-control review rules.
     Changes require API calls. No way to have branch-specific rules.

2. **In-repo file only** — All configuration in `.codereview.yml`.
   - Rejected because: Requires write access to the repo to change rules.
     Can't set global defaults across multiple repos. Secrets (webhook
     tokens) can't be stored in the repo.

3. **Environment variables only** — Config via `.env` or env vars.
   - Rejected because: Not per-repo. Can't have different rules for different
     repos in the same deployment.

### Decision

**Layered config with precedence**: `.codereview.yml` in repo root (highest)
→ `RepoConfig.review_rules` in DB (medium) → application defaults (lowest).

The `config_service.py` merges these layers. Developers can override any
DB-level setting by committing a `.codereview.yml` to their repo.

### Consequences

- (+) Developers can version-control their review rules
- (+) Admins can set org-wide defaults via DB
- (+) App provides sensible defaults out of the box
- (+) Branch-specific rules possible (fetch `.codereview.yml` from PR head)
- (-) Config loading adds a DB call + file fetch per review (acceptable — cached)
- (-) Merge semantics need clear documentation (which fields override which)

---

## ADR-011: Provider-Agnostic Multi-Language Review

**Status**: Accepted

### Context

Code repositories contain multiple programming languages. The review tool
should analyze all languages present in a PR without requiring language-specific
parsers or ASTs.

### Alternatives Considered

1. **Language-specific AST parsers** — Parse code into ASTs, run language-specific
   linting rules, then send structured data to LLM.
   - Rejected because: Massive scope explosion. Each language needs its own
     parser, rule set, and integration. Defeats the purpose of using an LLM
     for general-purpose review.

2. **Tree-sitter based parsing** — Universal parser for multiple languages.
   - Rejected because: Still requires per-language query definitions. Adds
     complexity without clear benefit — LLMs understand code directly.

3. **Linters as pre-processing** — Run existing linters (ruff, eslint), send
   lint results + diff to LLM for synthesis.
   - Considered for future: Could complement LLM review with deterministic
     checks. Not needed for MVP.

### Decision

**LLM-native review**. The diff is sent directly to the LLM with context
about the file's language (detected from extension). The LLM's training
covers all major programming languages. Language is used for prompt context,
not for parsing.

### Consequences

- (+) Works with any language out of the box
- (+) No parser maintenance burden
- (+) LLM understands code semantics, not just syntax
- (-) LLM may miss language-specific idioms (acceptable — improves with
  better prompts and few-shot examples)
- (-) No deterministic linting (can be added as pre-processing in future)

---

## ADR-012: Both Line-Level Comments and PR Summary

**Status**: Accepted

### Context

Review output needs to be actionable for developers. Two levels of granularity
serve different purposes.

### Alternatives Considered

1. **Line-level comments only** — Individual inline suggestions.
   - Rejected because: No big-picture view. Developers miss architectural or
     cross-file concerns. No way to triage overall PR quality.

2. **PR summary only** — High-level report with severity ratings.
   - Rejected because: Not actionable. Developers need to know exactly which
     lines to change.

### Decision

**Both**. Each review produces:
- Inline `ReviewComment` objects (file, line, suggestion, severity, category)
  posted as PR/MR review comments
- A top-level `summary` string posted as a PR/MR comment for overall assessment

### Consequences

- (+) Developers get both actionable line suggestions and big-picture context
- (+) Summary can be used for automated PR approval rules in the future
- (+) Comments and summary serve different audiences (reviewer vs author)
- (-) Two LLM calls per review (chunks for comments, then summary) — acceptable
  for quality; can optimize with single-call structured output later

---

## ADR-013: String Enum for VCS Type Per Repo

**Status**: Accepted

### Context

`RepoConfig` needs to know which VCS provider a repository uses. This affects
which `VCSProvider` implementation is loaded and how webhooks are processed.

### Alternatives Considered

1. **Separate tables/models per VCS** — `GitHubRepoConfig`, `GitLabRepoConfig`.
   - Rejected because: Duplicates shared fields (owner, name, review rules).
     Querying across all repos requires UNION queries. Adding a VCS means
     adding a new model + new API endpoints.

2. **Auto-detect from webhook payload** — Don't store VCS type, detect it
   every time from webhook headers.
   - Rejected because: Can't query "show me all GitHub repos" without scanning
     webhook logs. Can't pre-load the right VCS provider without a webhook
     context.

### Decision

**String enum `VCSEnum`** stored on `RepoConfig.vcs_type`. Values: `"github"`,
`"gitlab"`. Used by the factory to select the provider implementation.

### Consequences

- (+) Single model for all VCS providers
- (+) Easy to query and filter by VCS type
- (+) Adding a VCS means adding an enum value + implementation
- (-) All VCS providers must fit the same `RepoConfig` schema (some providers
  may need extra fields — handled by optional fields or a separate config
  document)

---

## ADR-014: PyGithub for GitHub API

**Status**: Accepted

### Context

Need a Python library to interact with GitHub's REST API (fetch diffs, post
PR review comments, get file contents, handle App authentication).

### Alternatives Considered

1. **httpx (manual)** — Raw HTTP calls to GitHub API.
   - Rejected because: Must handle pagination, rate limiting, error formats,
     authentication manually. More code, more bugs, no type hints.

2. **github-sdk-py** — GitHub's official Python SDK.
   - Rejected because: Less mature than PyGithub, smaller community, fewer
     examples.

3. **PyGitHub** — Most popular Python GitHub library.
   - Selected because: Mature, well-documented, typed, handles auth/pagination
     automatically. Wraps the full GitHub REST API.

### Decision

**PyGithub** for all GitHub API interactions, wrapped in `app/vcs/github/client.py`.

### Consequences

- (+) Mature, well-tested library
- (+) Automatic pagination and rate limit handling
- (+) Typed, good IDE support
- (+) Handles GitHub App authentication
- (-) Synchronous by default (wrapped in `asyncio.to_thread()` or use
  `githubkit` for native async in future)

---

## ADR-015: python-gitlab for GitLab API

**Status**: Accepted

### Context

Same need as ADR-014 but for GitLab's API.

### Alternatives Considered

1. **httpx (manual)** — Same rejection as ADR-014.
2. **python-gitlab** — Official GitLab Python client.
   - Selected because: Maintained by GitLab, full API coverage, typed.

### Decision

**python-gitlab** for all GitLab API interactions, wrapped in
`app/vcs/gitlab/client.py`.

### Consequences

- (+) Official library, maintained by GitLab
- (+) Full API coverage (MRs, diffs, comments, webhooks)
- (+) Supports both GitLab.com and self-hosted instances
- (-) Synchronous (same mitigation as PyGithub)

---

## ADR-016: Pydantic Settings for Configuration

**Status**: Accepted

### Context

Application configuration (database URLs, API keys, feature flags) needs to
come from environment variables with validation and defaults.

### Alternatives Considered

1. **Raw `os.environ`** — Direct environment variable access.
   - Rejected because: No validation, no defaults, no type coercion. Runtime
     crashes from missing/malformed env vars.

2. **Dynconf / dynaconf** — Multi-source config (env, files, vault).
   - Rejected because: Overkill for MVP. Pydantic Settings handles env vars
     + `.env` files, which is all we need.

3. **python-decouple** — Another config library.
   - Rejected because: Pydantic Settings is maintained by the same team as
     Pydantic, which we already use. No extra dependency.

### Decision

**Pydantic `BaseSettings`** in `app/config.py`. Reads from environment variables
with `.env` file support. Validates types, provides defaults, and fails fast
on startup if required vars are missing.

### Consequences

- (+) Type-safe configuration
- (+) Fails fast on missing/invalid config
- (+) `.env` file support for local development
- (+) Same Pydantic ecosystem as the rest of the app
- (-) Secrets in env vars (acceptable — standard practice, use cloud secret
  managers in production)

---

## ADR-017: Idempotent Webhook Processing

**Status**: Accepted

### Context

VCS platforms (especially GitHub) redeliver webhooks on timeout or failure.
The system must not create duplicate reviews for the same PR commit.

### Alternatives Considered

1. **No idempotency** — Create a new review on every webhook delivery.
   - Rejected because: Duplicate reviews = duplicate comments on the PR.
     Wastes LLM API calls. Confusing for developers.

2. **In-memory deduplication** — Track recent webhook IDs in memory.
   - Rejected because: Lost on process restart. Doesn't work across multiple
     worker instances.

3. **Unique database index** — Unique constraint on the identifying fields.
   - Selected because: Database-enforced, works across instances, survives
     restarts.

### Decision

**Unique compound index** on `(repo_id, vcs_type, pr_number, head_sha)` in the
`Review` model. Webhook handler performs an upsert: if a review with these keys
exists, return its ID instead of creating a duplicate.

### Consequences

- (+) Database-guaranteed idempotency
- (+) No in-memory state required
- (+) Works across multiple API instances
- (-) Race condition possible if two webhooks arrive simultaneously (handled
  by upsert atomicity in MongoDB)
