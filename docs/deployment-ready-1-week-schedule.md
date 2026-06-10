# Deployment-Ready 1-Week Build Schedule

## Goal

Upgrade the completed MVP into a deployment-ready, free-to-run Agentic AI Incident Commander using real LangGraph, PostgreSQL/pgvector, Redis, Ollama, Docker Compose, Prometheus/Grafana, and GitHub Actions.

This plan assumes 4 to 6 focused hours per day.

## Target Stack

- Frontend: React, Vite, TypeScript, React Router, TanStack Query, Stitch-derived CSS
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn
- Agentic AI: LangGraph, checkpointing, human-in-the-loop approval nodes
- RAG: PostgreSQL + pgvector, SentenceTransformers, hybrid keyword/vector retrieval
- LLM: Ollama local provider with deterministic fallback mode
- Cache: Redis
- Observability: Prometheus, Grafana, structured logs
- Deployment: Docker Compose
- CI/CD: GitHub Actions

## Day 1: Real LangGraph Conversion

### Goal

Replace the manual LangGraph-style workflow with actual LangGraph orchestration while keeping the existing API behavior stable.

### Tasks

- Add LangGraph dependency.
- Define typed incident investigation state.
- Convert current workflow functions into LangGraph nodes:
  - Alert Intake
  - Metrics
  - Logs
  - GitHub/Deploy
  - Runbook RAG
  - Evidence Ranking
  - Root Cause
  - Mitigation
  - Approval
  - Postmortem
- Add conditional edges for:
  - approval required
  - approved
  - rejected
  - more investigation required
- Preserve existing trace output shape for the frontend.

### Output

- Real LangGraph workflow module.
- Existing tests passing.
- New tests proving LangGraph node execution order.

### Verification

```powershell
pytest -q
python -m evals.evaluate_demo
```

## Day 2: PostgreSQL, SQLAlchemy, And Alembic

### Goal

Replace in-memory persistence with database-backed incident state.

### Tasks

- Add PostgreSQL dependency stack.
- Create SQLAlchemy models for:
  - alerts
  - incidents
  - evidence
  - hypotheses
  - recommendations
  - approvals
  - postmortems
  - timeline events
  - agent traces
  - runbook chunks
- Add Alembic migration setup.
- Add repository/data-access layer.
- Add seed command for demo data.
- Keep a test-friendly fallback path.

### Output

- Persistent incident store.
- Migration files.
- Seed script.

### Verification

```powershell
alembic upgrade head
pytest -q
```

## Day 3: pgvector And Runbook RAG Upgrade

### Goal

Upgrade retrieval from keyword-only to hybrid keyword plus vector retrieval.

### Tasks

- Enable pgvector extension.
- Add SentenceTransformers embedding pipeline.
- Store runbook chunk embeddings in PostgreSQL.
- Add runbook ingestion command.
- Implement hybrid retriever:
  - keyword score
  - vector similarity
  - service match
  - incident relevance
- Return citations for root-cause and mitigation agents.

### Output

- pgvector-backed runbook retrieval.
- Runbook ingestion command.
- Retrieval eval cases.

### Verification

```powershell
python -m backend.app.ingest_runbooks
pytest -q
python -m evals.evaluate_demo
```

## Day 4: Ollama LLM Layer And Deterministic Fallback

### Goal

Add local LLM-backed generation without making tests or demos depend on paid cloud services.

### Tasks

- Add LLM provider abstraction.
- Add Ollama adapter.
- Add deterministic fallback adapter.
- Add prompt templates for:
  - root-cause synthesis
  - mitigation explanation
  - postmortem writing
- Add environment variables:
  - `LLM_PROVIDER`
  - `OLLAMA_BASE_URL`
  - `OLLAMA_MODEL`
- Keep tests deterministic by default.

### Output

- Local LLM support.
- Fallback mode for stable tests.
- Cleaner generated explanations when Ollama is running.

### Verification

```powershell
pytest -q
python -m evals.evaluate_demo
```

Optional Ollama check:

```powershell
ollama run llama3.1
```

## Day 5: Docker Compose Full Stack

### Goal

Make the full project runnable with one command.

### Tasks

- Add backend Dockerfile.
- Add frontend Dockerfile.
- Add `docker-compose.yml` with:
  - api
  - frontend
  - postgres with pgvector
  - redis
  - prometheus
  - grafana
- Add `.env.example`.
- Add startup/health checks.
- Add database migration/seed instructions.

### Output

- Full local deployment stack.
- One-command local demo path.

### Verification

```powershell
docker compose up --build
```

Then verify:

- Frontend opens.
- Backend health endpoint works.
- Database persists incidents.
- Redis is reachable.

## Day 6: Observability, Frontend Routing, And CI

### Goal

Add production-style project quality: observability, cleaner frontend architecture, and CI checks.

### Tasks

- Add structured JSON logging.
- Add request IDs.
- Add Prometheus metrics endpoint.
- Track:
  - alert ingestion count
  - workflow duration
  - agent step duration
  - evidence count
  - approval decisions
  - postmortem generation count
- Add Grafana dashboard JSON.
- Add React Router routes:
  - `/incidents`
  - `/incidents/:id`
  - `/simulation`
  - `/traces`
  - `/health`
  - `/runbooks`
  - `/archive`
  - `/team`
  - `/postmortem`
- Add TanStack Query API hooks.
- Add GitHub Actions for:
  - backend tests
  - evals
  - frontend build
  - Docker build validation

### Output

- Observability-ready backend.
- Route-based frontend.
- CI workflow.

### Verification

```powershell
pytest -q
cd frontend
npm.cmd run build
```

Check GitHub Actions after push.

## Day 7: Final Demo Polish And Portfolio Readiness

### Goal

Make the project interview-ready and GitHub-ready.

### Tasks

- Update README with:
  - final deployment-ready stack
  - Docker Compose setup
  - architecture diagram
  - LangGraph workflow explanation
  - screenshots
  - eval results
  - demo script
- Capture final screenshots of all pages:
  - Incident Overview
  - Alert Simulation Hub
  - Investigation
  - Agent Tracing
  - System Health
  - Runbook Library
  - Archive
  - Team Access
  - Postmortem
- Update resume bullet.
- Add final limitations and future upgrades.
- Run complete verification.

### Output

- Deployment-ready GitHub repository.
- Final demo script.
- Final README.
- Resume-ready project wording.

### Verification

```powershell
pytest -q
python -m evals.evaluate_demo
cd frontend
npm.cmd run build
docker compose config
```

## Final Acceptance Criteria

- Real LangGraph is used in code.
- Incidents persist in PostgreSQL.
- Runbooks use pgvector-backed retrieval.
- Ollama can be used locally without cloud spend.
- The system has deterministic fallback mode.
- Docker Compose runs the full stack.
- Prometheus/Grafana observability exists.
- GitHub Actions runs tests, evals, and frontend build.
- Frontend includes all Stitch-derived screens.
- README clearly explains the architecture and demo flow.

## Final Resume Bullet

Built a deployment-ready agentic incident response platform using LangGraph, FastAPI, React, PostgreSQL/pgvector, Redis, Ollama, Docker Compose, Prometheus/Grafana, runbook RAG, human-in-the-loop approvals, deterministic evals, and automated postmortem generation for e-commerce API incidents.
