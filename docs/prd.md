# Agentic AI Incident Commander PRD

## 1. Product Summary

Agentic AI Incident Commander is an agentic incident response platform for an e-commerce API. It detects and investigates production incidents by correlating alerts, logs, metrics, traces, GitHub changes, deployment history, and runbooks. The current MVP proves the workflow with mocked data; the deployment-ready target uses real LangGraph, PostgreSQL/pgvector, Redis, Docker Compose, Ollama or free hosted LLM providers, and Prometheus/Grafana.

The first demo scenario focuses on a checkout/payment API incident where latency and failed payments spike after a recent deployment or database bottleneck.

## 2. Problem Statement

Production incidents are time-sensitive, but engineers often lose critical minutes jumping between monitoring dashboards, logs, traces, deployment records, GitHub commits, runbooks, and team communication channels. During an e-commerce checkout incident, this delay can directly impact revenue and customer trust.

The core problem:

- Alerts tell teams that something is wrong but rarely explain why.
- Logs, metrics, traces, commits, and runbooks are spread across separate systems.
- Engineers must manually correlate deployment timing, error patterns, infrastructure behavior, and known failure modes.
- Root-cause analysis and postmortems are often written after the fact, when details are already scattered.
- Risky mitigations like rollback or traffic throttling require human approval, but teams need better evidence before making that call.

## 3. Target Users

- **SRE / On-call engineer:** Needs fast investigation, evidence, mitigation options, and a clear approval workflow.
- **Backend engineer:** Needs code/deployment context, likely affected services, and suspected root cause.
- **Engineering manager:** Needs incident summary, user impact, timeline, mitigation status, and postmortem output.

## 4. Product Goal

Build a polished incident commander where a checkout/payment alert triggers an agentic investigation. The system should gather evidence, reason over it, recommend a mitigation, ask for human approval, and generate a postmortem.

The MVP proves the workflow. The deployment-ready version should add real LangGraph orchestration, persistent storage, vector retrieval, Dockerized services, free/local LLM support, observability, and CI/CD.

## 5. Confirmed Free Deployment-Ready Stack

- **Frontend:** React, Vite, TypeScript, React Router, TanStack Query, Stitch-derived CSS.
- **Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn.
- **Agent orchestration:** LangGraph with checkpointing and human-in-the-loop approval nodes.
- **LLM provider:** Ollama locally, with optional free hosted fallback through Groq, Gemini, or OpenRouter.
- **Embeddings:** SentenceTransformers.
- **Database:** PostgreSQL with pgvector.
- **Cache/workflow coordination:** Redis.
- **RAG:** Hybrid keyword plus vector retrieval over Markdown runbooks.
- **Observability:** Prometheus, Grafana, structured logs.
- **Deployment:** Docker Compose for local deployment-ready demo.
- **CI/CD:** GitHub Actions for tests, evals, frontend build, and Docker validation.

## 6. Incident Scenario

**Incident:** Checkout API latency and payment failures spike.

**Possible causes represented in mock data:**

- A recent deployment changed payment retry logic.
- Database connection pool saturation increased checkout latency.
- Payment provider API timeout errors increased.
- Checkout service logs show repeated `PAYMENT_AUTH_TIMEOUT` and `DB_POOL_EXHAUSTED` events.
- Runbooks contain guidance for checkout latency, payment gateway failures, and rollback procedures.

The system should identify the most likely cause using evidence rather than guessing.

## 7. Core Features

### Alert Ingestion

- Accept a mock alert payload from Datadog, Prometheus, or Grafana-style input.
- Support Prometheus-compatible alert ingestion in the deployment-ready version.
- Create an incident record with severity, service, metric, timestamp, and alert details.
- Start the LangGraph investigation workflow automatically.

### Agentic Investigation

- Query metrics for latency, error rate, throughput, CPU, memory, and database pool usage.
- Query logs for error patterns and recent abnormal events.
- Query deployment history and GitHub commit metadata.
- Retrieve relevant runbook sections using hybrid keyword plus pgvector RAG.
- Produce evidence-backed root-cause hypotheses.

### Mitigation Recommendation

- Recommend one or more actions such as rollback, scale database pool, disable risky feature flag, or monitor only.
- Assign confidence and risk level to each action.
- Explain the evidence behind each recommendation.

### Human Approval

- Require explicit user approval before any risky mitigation is marked as executed.
- Support approve, reject, or request more investigation.
- Store the decision in the incident timeline.

### Postmortem Generation

- Generate a structured postmortem with incident summary, timeline, impact, root cause, mitigation, follow-up actions, and unresolved questions.
- Allow export as Markdown.

### Persistence And Checkpointing

- Persist incidents, evidence, recommendations, approvals, traces, and postmortems in PostgreSQL.
- Persist runbook chunks and embeddings in PostgreSQL/pgvector.
- Use LangGraph checkpointing so interrupted investigations can resume.
- Use Redis for session/workflow coordination where helpful.

### Evaluation And Observability

- Run deterministic workflow evals locally.
- Track graph step completion, evidence coverage, root-cause confidence, approval gating, and postmortem section coverage.
- Expose backend/service metrics to Prometheus.
- Visualize operational metrics in Grafana.

## 8. Non-Goals

- Paid AWS deployment or AWS Bedrock usage.
- Real production access to Datadog, Kubernetes, or private infrastructure in the first deployment-ready build.
- Automatic execution of real rollback or infrastructure changes.
- Full enterprise access control.
- Supporting every service architecture or every incident type.
- Guaranteeing perfect root-cause diagnosis.

## 9. Success Metrics

- Investigation completes within 60 seconds in the local demo.
- Root-cause hypothesis references at least three evidence sources.
- Recommended mitigation includes confidence, risk, and approval requirement.
- Postmortem includes a coherent incident timeline and follow-up actions.
- Demo user can understand the incident without manually opening logs, metrics, runbooks, or GitHub.
- LangGraph workflow can resume from persisted checkpoint state.
- CI passes backend tests, evals, and frontend build.
- Docker Compose can start the complete local stack.

## 10. Demo Acceptance Criteria

- A mock checkout/payment alert can be submitted through API or dashboard.
- The system creates an incident and starts the LangGraph workflow.
- The dashboard shows investigation progress by agent step.
- Metrics, logs, deployment, GitHub, and runbook evidence are visible.
- Root-cause hypothesis is generated with evidence citations.
- At least two mitigation options are ranked.
- User can approve or reject a recommended action.
- Postmortem is generated after approval or rejection.
- All data can run locally with Docker and mock fixtures.
- PostgreSQL stores incidents, evidence, approvals, and postmortems.
- pgvector stores runbook embeddings.
- LangGraph is used as the actual workflow engine, not only a manually coded workflow.
- No paid cloud service is required.

## 11. Resume Positioning

Suggested resume bullet:

> Built a deployment-ready agentic incident response platform using LangGraph, FastAPI, React, PostgreSQL/pgvector, Ollama, Docker Compose, Prometheus/Grafana, runbook RAG, human-in-the-loop approvals, deterministic evals, and automated postmortem generation for e-commerce API incidents.
