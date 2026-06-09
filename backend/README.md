# Backend

Python backend workspace for Agentic AI Incident Commander.

Day 1 includes:

- Pydantic models for the core incident data objects.
- A fixture loader for mock alerts, metrics, logs, deployments, commits, and runbooks.

Day 2 includes:

- FastAPI app.
- In-memory incident store seeded from fixtures.
- Incident, evidence, recommendation, approval, and postmortem APIs.

Day 3 includes:

- Deterministic LangGraph-style investigation workflow.
- Specialist agent steps for alert intake, metrics, logs, deploys, runbooks, root cause, mitigation, and approval.
- Agent trace records for each workflow step.

Day 4 includes:

- Runbook retrieval over local Markdown chunks with keyword expansion and result diversity.
- Evidence ranking by relevance, service match, time proximity, severity, and source agreement.
- A visible evidence-ranking workflow step before root-cause synthesis.

Day 6 includes:

- Approval lifecycle for approve, reject, and request-more-investigation decisions.
- Postmortem generation from current incident state, evidence, timeline, approvals, and follow-up actions.
- Deterministic eval harness for graph completeness, evidence coverage, confidence, approval gating, and postmortem coverage.

## Deployment-Ready Upgrade Target

The current backend is the completed MVP. The next implementation target is:

- Replace the manual LangGraph-style workflow with real LangGraph.
- Replace the in-memory store with PostgreSQL using SQLAlchemy and Alembic.
- Add pgvector-backed runbook retrieval with SentenceTransformers embeddings.
- Add Redis for workflow/session coordination.
- Add Ollama or free hosted LLM provider adapters.
- Add Prometheus metrics and Grafana dashboard support.
- Run the full backend stack through Docker Compose.

## Run

```powershell
uvicorn backend.app.main:app --reload
```

## Key Endpoints

- `GET /health`
- `POST /alerts`
- `GET /incidents`
- `GET /incidents/{incident_id}`
- `GET /incidents/{incident_id}/timeline`
- `GET /incidents/{incident_id}/evidence`
- `GET /incidents/{incident_id}/hypotheses`
- `GET /incidents/{incident_id}/recommendations`
- `GET /incidents/{incident_id}/traces`
- `POST /incidents/{incident_id}/investigate`
- `POST /incidents/{incident_id}/approvals`
- `GET /incidents/{incident_id}/approvals`
- `GET /incidents/{incident_id}/postmortem`
- `GET /runbooks`
- `GET /system-health`
- `POST /dev/reset`
