# Demo Script: Agentic AI Incident Commander

Target length: 5 to 6 minutes.

## 1. Start The App

Preferred full-stack path:

```powershell
docker compose up --build
```

If Docker Desktop is not running, use the local developer path.

Backend:

```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:5173
```

Optional observability views:

```text
http://127.0.0.1:8000/metrics
http://127.0.0.1:9090
http://127.0.0.1:3000
```

## 2. Opening Pitch

"This project solves a production incident response problem. Instead of asking an engineer to manually check alerts, logs, metrics, deployments, GitHub commits, and runbooks, the system runs a multi-agent investigation workflow and produces an evidence-backed mitigation recommendation."

Add:

"It is deployment-ready locally: LangGraph orchestration, FastAPI, React, PostgreSQL/pgvector through Docker Compose, hybrid runbook RAG, optional Ollama, Prometheus/Grafana, and GitHub Actions CI."

## 3. Incident Overview

Show the active checkout incident.

Mention:

- The domain is an e-commerce checkout/payment API.
- The alert is high latency with payment failures.
- The dashboard is evidence-first, not chatbot-first.
- The topology and agent rail show system stress and investigation progress.

## 4. Investigation View

Open the Investigation page.

Point out the 9 workflow steps:

- Alert Intake Agent
- Metrics Agent
- Logs Agent
- GitHub/Deploy Agent
- Runbook RAG Agent
- Evidence Ranking Agent
- Root Cause Agent
- Mitigation Agent
- Approval Agent

Explain:

"Each step updates shared incident state. The workflow gathers evidence first, ranks it, then generates the root-cause hypothesis and mitigation recommendation."

Mention:

- The workflow uses real LangGraph, not a hand-written loop.
- Each node emits a trace record.
- Workflow and agent step durations are exported as Prometheus metrics.

## 5. Root Cause And Mitigation

Show the hypothesis and ranked mitigation panel.

Say:

"The top hypothesis is database connection pool saturation after a payment retry deployment. The recommendation is rollback because the deployment, DB pool metric, logs, commit risk notes, and runbook all point to the same cause."

## 6. Human Approval

Click Approve, Reject, or More Evidence.

Say:

"The system does not silently execute risky actions. It pauses for human approval and records the decision in the timeline."

## 7. Postmortem

Open the Postmortem page.

Point out:

- Alert details
- Impact
- Likely root cause
- Recommended mitigation
- Human approval trail
- Evidence
- Timeline
- Follow-up actions

## 8. Runbooks And System Health

Open Runbooks.

Say:

"The Runbook RAG page shows the knowledge sources used by the agent. Retrieval is hybrid keyword plus vector scoring, with PostgreSQL/pgvector support in the Docker stack and a deterministic local embedding fallback for stable tests."

Open System Health.

Say:

"The System Health page shows service-level impact and gives the incident commander context beyond a single alert."

Open Agent Tracing.

Say:

"The tracing view shows the LangGraph state at each step: evidence count, active node, top hypothesis, recommendation, and approval requirement."

Open Team Access.

Say:

"The team view shows how approval roles, integrations, and mitigation policies would be represented in an incident workflow."

## 9. Evaluation

Run:

```powershell
python -m evals.evaluate_demo
```

Say:

"I added deterministic evals to validate graph completeness, evidence source coverage, root-cause confidence, approval gating, and postmortem section coverage."

Also run:

```powershell
pytest -q
cd frontend
npm.cmd run build
docker compose config
```

Say:

"The project currently has 34 automated tests and a deterministic eval score of 0.976."

## 10. Closing Pitch

"This demonstrates the real agentic AI pattern: tool use, multi-step stateful orchestration, retrieval, evidence ranking, LLM-backed synthesis with deterministic fallback, human-in-the-loop control, observability, CI, and automated incident documentation."
