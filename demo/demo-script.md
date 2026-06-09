# Demo Script: Agentic AI Incident Commander

Target length: 4 to 5 minutes.

## 1. Start The App

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

## 2. Opening Pitch

"This project solves a production incident response problem. Instead of asking an engineer to manually check alerts, logs, metrics, deployments, GitHub commits, and runbooks, the system runs a multi-agent investigation workflow and produces an evidence-backed mitigation recommendation."

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

"The Runbook RAG page shows the knowledge sources used by the agent. In production this could be backed by internal docs, Confluence, or incident runbooks."

Open System Health.

Say:

"The System Health page shows service-level impact and gives the incident commander context beyond a single alert."

## 9. Evaluation

Run:

```powershell
python -m evals.evaluate_demo
```

Say:

"I added deterministic evals to validate graph completeness, evidence source coverage, root-cause confidence, approval gating, and postmortem section coverage."

## 10. Closing Pitch

"This is an MVP, but it demonstrates the real agentic AI pattern: tool use, multi-step reasoning, stateful orchestration, evidence-backed recommendations, human-in-the-loop control, and automated incident documentation."
