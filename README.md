# AI-Powered PR Review Assistant

An AI-native code review platform that automatically analyzes GitHub PRs and GitLab MRs for
**security**, **performance**, **code quality**, and **test coverage** issues, posts a
summary comment back to the PR/MR, sets a commit status that can block merge on critical
findings, and exposes the full detail through a React dashboard.

## Highlights

- **Multi-agent review architecture** — four specialist agents (security, performance,
  code quality, testing), each with its own system prompt and its own Temporal child
  workflow so failures are isolated and retried independently.
- **LangGraph inside Temporal** — each agent runs a compiled LangGraph pipeline
  (`retrieve → analyze → validate`) for its own reasoning loop; Temporal owns the durable
  cross-agent orchestration, retries, and audit trail.
- **RAG over project coding standards** — a lightweight retriever pulls relevant snippets
  from `docs/standards/*.md` (security, performance, code quality, testing) into each
  agent's prompt so findings cite project-specific rules, not just the model's priors.
- **Structured, validated LLM output** — every finding is parsed into a Pydantic `Finding`
  model with a schema-enforced shape (`severity`, `file`, `line_number`, `issue`,
  `explanation`, `impact`, `recommendation`, `confidence`); malformed entries are dropped
  with a warning rather than crashing the review.
- **Durable, replayable workflows** — one Temporal entity workflow per PR/MR, one
  re-review per pushed commit via `new_commit` signal, `continue_as_new` between rounds,
  independent retry policies per activity, idempotent PR comments keyed by a hidden
  marker.
- **Round-over-round diff** — the comment tells you which issues were resolved, which are
  new, and which are still present since the previous review round.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design (workflow diagram,
agent graph, RAG retriever, VCS abstraction, data model, what's deliberately deferred past
this MVP).

## Stack

- **Backend:** Python 3.11, FastAPI, [Temporal](https://temporal.io/) (Python SDK),
  [LangGraph](https://langchain-ai.github.io/langgraph/), [Groq](https://console.groq.com)
  (`llama-3.3-70b-versatile`) for the LLM, PostgreSQL + SQLAlchemy 2.
- **Frontend:** React 18, Vite, TypeScript, Recharts.
- **Tooling:** [uv](https://docs.astral.sh/uv/) for Python deps,
  [pnpm](https://pnpm.io/) for JS deps, Docker Compose for the local stack.

Development was assisted end-to-end by **Cursor**, **Claude Code**, and **GitHub Copilot**
for specification, implementation, debugging, testing, and documentation.

## Run it locally

1. Copy the env template and add your Groq API key:

   ```bash
   cp .env.example .env
   # edit .env, set GROQ_API_KEY=...
   ```

   `VCS_MODE=mock` (the default) needs no GitHub/GitLab tokens — the worker serves a fixed
   illustrative diff (a backend service change + a weak-assertion test) and logs comments
   instead of posting them, so you can exercise the whole pipeline — Temporal fan-out,
   LangGraph per-agent graph, RAG retrieval over `docs/standards/`, Groq LLM calls, and
   dashboard rendering — with zero repo credentials.

2. Bring up the stack:

   ```bash
   docker compose up --build
   ```

   Starts: Postgres, Temporal server + Web UI, `webhook-gateway`, `worker`, `api`,
   `frontend`.

3. Trigger a review (no live webhook needed):

   ```bash
   python3 scripts/simulate_webhook.py --provider github
   # or
   python3 scripts/simulate_webhook.py --provider gitlab
   ```

4. Inspect the result:
   - **Temporal UI** — <http://localhost:8088> — workflow execution, per-agent child
     workflows, activity retries, timing.
   - **Dashboard** — <http://localhost:5173> — review list, per-finding detail, analytics
     by category and severity.
   - **API directly** — `curl http://localhost:8001/api/reviews`.
   - **Worker logs** — `docker compose logs -f worker` — the mock VCS client logs the
     comment it "would have" posted, and the RAG `retrieve` node logs which standards
     snippets were pulled for each agent.

### Going live against a real repo

Set `VCS_MODE=live`, fill in `GITHUB_TOKEN`/`GITLAB_TOKEN` (and the matching
`*_WEBHOOK_SECRET`) in `.env`, point your repo's webhook at
`http(s)://<host>:8000/webhooks/github` (or `/webhooks/gitlab`), and restart the stack.

## Repository layout

```
libs/shared/                        Shared Pydantic schemas, SQLAlchemy models, config
services/webhook-gateway/           FastAPI: verifies webhooks, starts PRReviewWorkflow
services/worker/                    Temporal worker
  app/agents/                         4 review agents (security, performance, code_quality, testing)
  app/agents/graph.py                 LangGraph per-agent pipeline: retrieve → analyze → validate
  app/rag/                            Keyword-overlap retriever over docs/standards/
  app/workflows/                      PRReviewWorkflow + per-agent child workflows
  app/activities/                     VCS, agent, persistence activities
services/api/                       Read-only FastAPI dashboard API
frontend/                           React + Vite dashboard
scripts/                            simulate_webhook.py + sample GitHub/GitLab payloads
docs/standards/                     Coding-standards corpus consumed by the RAG retriever
docs/ARCHITECTURE.md                Full design writeup
```
