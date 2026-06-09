# Roadmap

## 1. Roadmap Summary

The project now has a working MVP. The next goal is to upgrade it into a free, deployment-ready agentic AI platform using real LangGraph, PostgreSQL/pgvector, Redis, Ollama, Docker Compose, Prometheus/Grafana, and GitHub Actions.

No AWS spend is required.

## Current Baseline: Completed MVP

Already implemented:

- FastAPI backend.
- React/Vite dashboard based on Stitch screens.
- Mock checkout/payment incident fixtures.
- Deterministic LangGraph-style agent workflow.
- Runbook retrieval and evidence ranking.
- Human approval flow.
- Markdown postmortem generation.
- pytest suite.
- Deterministic eval harness.
- Portfolio README and demo script.
- Public GitHub repository.

## Phase 1: Convert Workflow To Real LangGraph

Goal:

- Replace the manual deterministic workflow with actual LangGraph state graph orchestration.

Deliverables:

- LangGraph dependency added.
- Typed incident investigation state.
- Nodes for:
  - Alert Intake Agent
  - Metrics Agent
  - Logs Agent
  - GitHub/Deploy Agent
  - Runbook RAG Agent
  - Evidence Ranking Agent
  - Root Cause Agent
  - Mitigation Agent
  - Approval Agent
  - Postmortem Agent
- Conditional edges for approve, reject, and more investigation.
- Checkpointing design for workflow resume.

Acceptance criteria:

- Tests prove real LangGraph executes the workflow.
- Existing API behavior remains compatible with the frontend.
- The workflow pauses at human approval and resumes after a decision.

## Phase 2: Add PostgreSQL, SQLAlchemy, And Alembic

Goal:

- Replace the in-memory incident store with persistent storage.

Deliverables:

- PostgreSQL Docker service.
- SQLAlchemy models for alerts, incidents, evidence, hypotheses, recommendations, approvals, postmortems, runbook chunks, and agent traces.
- Alembic migration setup.
- Repository/data-access layer.
- Seed script for demo data.

Acceptance criteria:

- Restarting the backend does not erase incidents.
- Tests can run against a temporary test database or isolated SQLite fallback.
- Existing endpoints read/write from the database.

## Phase 3: Add pgvector And Local Runbook Embeddings

Goal:

- Upgrade runbook retrieval from keyword-only retrieval to hybrid keyword plus vector retrieval.

Deliverables:

- pgvector extension enabled in PostgreSQL.
- SentenceTransformers embedding pipeline.
- Runbook ingestion command.
- Hybrid retriever that combines lexical score and vector similarity.
- Citation metadata for retrieved chunks.

Acceptance criteria:

- Runbook chunks are stored with embeddings.
- Retrieval returns relevant checkout latency, DB pool, payment timeout, and rollback sections.
- Eval checks confirm source coverage and retrieval relevance.

## Phase 4: Add LLM Layer With Free Providers

Goal:

- Add optional LLM-backed summaries while keeping deterministic fallback mode.

Deliverables:

- Ollama provider adapter.
- Optional Groq/Gemini/OpenRouter provider adapter through environment variables.
- Prompt templates for:
  - Root-cause synthesis
  - Mitigation explanation
  - Postmortem narrative
- Deterministic fallback if no LLM is configured.

Acceptance criteria:

- Project runs without paid cloud services.
- `OLLAMA_BASE_URL` and model name can be configured through `.env`.
- Tests do not require an external LLM.
- Demo can use local Ollama when available.

## Phase 5: Docker Compose Deployment

Goal:

- Make the complete stack runnable with one command.

Deliverables:

- Backend Dockerfile.
- Frontend Dockerfile.
- `docker-compose.yml` with:
  - API
  - Frontend
  - PostgreSQL + pgvector
  - Redis
  - Prometheus
  - Grafana
  - Optional Ollama service or host Ollama configuration
- `.env.example`.
- Health checks.

Acceptance criteria:

- `docker compose up --build` starts the stack.
- Frontend can call backend inside Compose.
- Backend can connect to PostgreSQL and Redis.
- Prometheus and Grafana are reachable locally.

## Phase 6: Observability And Tracing

Goal:

- Show production-style operational visibility.

Deliverables:

- Structured JSON logging.
- Request IDs.
- Prometheus metrics endpoint.
- Metrics for:
  - Alert ingestion count
  - Workflow duration
  - Agent step duration
  - Evidence count
  - Approval decision count
  - Postmortem generation count
- Grafana dashboard JSON.

Acceptance criteria:

- Prometheus scrapes backend metrics.
- Grafana dashboard shows API and workflow metrics.
- Demo can show both the incident dashboard and system observability dashboard.

## Phase 7: Frontend Production Polish

Goal:

- Move from MVP UI to more maintainable frontend architecture.

Deliverables:

- TypeScript migration.
- React Router routes:
  - `/incidents`
  - `/incidents/:id`
  - `/health`
  - `/runbooks`
  - `/archive`
  - `/postmortems/:id`
- TanStack Query API hooks.
- API client module.
- Error/loading states.
- Better approval modal.

Acceptance criteria:

- User can deep-link to an incident.
- API state is cached and refetched cleanly.
- Approval actions update the UI without a full page reload.

## Phase 8: GitHub Actions CI/CD

Goal:

- Make the repository professional and deployment-ready.

Deliverables:

- CI workflow for backend tests.
- CI workflow for deterministic evals.
- CI workflow for frontend build.
- Docker build validation.
- Optional lint/type-check jobs.

Acceptance criteria:

- Every pull request runs tests, evals, and frontend build.
- Bad workflow or frontend changes fail CI.
- README shows local and Docker Compose setup clearly.

## Phase 9: Optional Free Hosting

Goal:

- Provide a hosted demo without AWS cost if a stable free option is available.

Free options to evaluate:

- Render free tier for backend.
- Railway free or limited credits.
- Fly.io free or limited allowance.
- Hugging Face Spaces for a demo container.
- GitHub Pages for static frontend only.

Acceptance criteria:

- Hosting does not require paid AWS resources.
- If free hosting is unreliable, local Docker Compose remains the official demo path.

## Future Upgrades

- Real Prometheus alert ingestion.
- Real GitHub API integration.
- Loki or OpenTelemetry log ingestion.
- Slack or Discord incident notifications.
- Authentication and role-based access control.
- Dry-run rollback integrations.
- Multi-service dependency graph.
- Learning loop from resolved incidents.
- LLM quality evaluation and model comparison.

## Recommended Build Order

1. Convert to real LangGraph.
2. Add PostgreSQL and Alembic.
3. Add pgvector and embedding-based runbook retrieval.
4. Add Ollama/free LLM provider abstraction.
5. Add Docker Compose.
6. Add Prometheus/Grafana observability.
7. Polish frontend architecture.
8. Add GitHub Actions CI.

This order preserves the current working demo while making the project more technically credible step by step.
