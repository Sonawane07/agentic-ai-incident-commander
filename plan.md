# Agentic AI Incident Commander: 1-Week End-to-End Build Plan

## Project Goal

Build a polished MVP of **Agentic AI Incident Commander**, an agentic incident response platform for an e-commerce checkout/payment API. The system will ingest a mock production alert, investigate logs/metrics/deployments/runbooks, generate root-cause hypotheses, recommend mitigations, request human approval, and generate a Markdown postmortem.

The project will be built in:

`C:\Users\User\Documents\Demo Project`

Reference materials:

- Product docs: `docs/`
- Stitch frontend screens: `stitch/`

## MVP Stack

- Backend: FastAPI
- Agent workflow: LangGraph-style graph workflow, with real LangGraph optional if dependency installation is available
- Persistence: in-memory or lightweight JSON persistence for MVP speed
- Production upgrade path: PostgreSQL
- Runbook retrieval: keyword/semantic-style retrieval over local runbook fixtures
- Frontend: Stitch-inspired runnable dashboard
- Testing: pytest
- Demo domain: e-commerce checkout/payment latency incident

## Day 1: Project Setup And Data Fixtures

### Goal

Create the project foundation and mock incident data needed for the full demo.

### Implementation Tasks

- Create backend and frontend folders.
- Add `README.md`, `requirements.txt`, and local run instructions.
- Define core data models based on `docs/data-flow.md`:
  - Alert
  - Incident
  - Evidence
  - RunbookChunk
  - Hypothesis
  - MitigationRecommendation
  - ApprovalDecision
  - Postmortem
- Create mock data fixtures:
  - Checkout/payment alert payload
  - Metrics for latency, error rate, throughput, CPU, memory, and DB pool usage
  - Logs with `PAYMENT_AUTH_TIMEOUT` and `DB_POOL_EXHAUSTED`
  - Deployment history
  - GitHub commit metadata
  - Runbook Markdown files
- Add a seed script or loader for demo data.

### Deliverables

- Project folder structure.
- Mock observability data.
- Runbook fixtures.
- Initial data model definitions.

### Done Checklist

- The project can load mock alert, metrics, logs, deployments, commits, and runbooks.
- The checkout/payment incident has enough evidence for one primary root cause and at least one alternative hypothesis.
- Data fields align with `docs/data-flow.md`.

## Day 2: FastAPI Backend

### Goal

Build the backend API layer for incidents, evidence, recommendations, approvals, and postmortems.

### Implementation Tasks

- Create FastAPI app.
- Add health endpoint.
- Add alert ingestion endpoint:
  - `POST /alerts`
- Add incident endpoints:
  - `GET /incidents`
  - `GET /incidents/{incident_id}`
  - `GET /incidents/{incident_id}/timeline`
- Add evidence endpoint:
  - `GET /incidents/{incident_id}/evidence`
- Add recommendation endpoint:
  - `GET /incidents/{incident_id}/recommendations`
- Add approval endpoint:
  - `POST /incidents/{incident_id}/approvals`
- Add postmortem endpoint:
  - `GET /incidents/{incident_id}/postmortem`
- Use in-memory or JSON persistence for MVP.
- Keep PostgreSQL as a documented production upgrade, not a Day 2 requirement.

### Deliverables

- Runnable FastAPI backend.
- Working API responses for seeded incident data.
- Basic API documentation through FastAPI Swagger.

### Done Checklist

- Backend starts locally.
- `POST /alerts` creates or triggers the checkout incident.
- Incidents, evidence, recommendations, approvals, and postmortem routes return valid JSON.
- API behavior matches the PRD and data-flow docs.

## Day 3: Agentic Investigation Workflow

### Goal

Implement the agentic investigation workflow that simulates LangGraph-style orchestration.

### Implementation Tasks

- Create a graph-style workflow with shared incident state.
- Implement these workflow nodes:
  - Alert Intake Agent
  - Metrics Agent
  - Logs Agent
  - GitHub/Deploy Agent
  - Runbook RAG Agent
  - Root Cause Agent
  - Mitigation Agent
  - Approval Agent
  - Postmortem Agent
- Store each agent step in the incident timeline.
- Keep outputs deterministic for a reliable portfolio demo.
- Add trace logs for agent step name, input summary, output summary, and timestamp.

### Deliverables

- Working investigation workflow.
- Timeline records for each agent step.
- Evidence generated from mocked logs, metrics, deployments, commits, and runbooks.

### Done Checklist

- A mock alert starts the workflow.
- Each agent step runs in the expected order.
- The workflow pauses when approval is required.
- Agent outputs are visible through backend APIs.

## Day 4: Runbook RAG And Evidence Ranking

### Goal

Add useful runbook retrieval and evidence-backed reasoning.

### Implementation Tasks

- Implement runbook chunking over local Markdown runbooks.
- Add keyword-based retrieval for MVP.
- Optionally add simple embedding/vector retrieval if dependencies are available.
- Score evidence using:
  - Service match
  - Time proximity
  - Severity
  - Relevance to alert
  - Agreement with other evidence sources
- Generate ranked hypotheses.
- Generate mitigation recommendations with:
  - Confidence
  - Risk level
  - Expected impact
  - Supporting evidence
  - Approval requirement

### Deliverables

- Runbook retrieval module.
- Evidence ranking module.
- Root-cause hypothesis output.
- Mitigation recommendation output.

### Done Checklist

- The system retrieves runbook sections for checkout latency, payment timeout, DB pool saturation, and rollback.
- Root-cause hypothesis cites at least three evidence sources.
- Recommendations are ranked and approval-gated.

## Day 5: Frontend Implementation

### Goal

Convert the Stitch visual direction into a runnable dashboard wired to the backend.

### Implementation Tasks

- Use Stitch screens from `stitch/` as the design reference.
- Implement dashboard views:
  - Incident overview
  - Investigation detail
  - System health
  - Incident archive
  - Runbook RAG library
  - Incident postmortem
- Wire UI to backend APIs.
- Show investigation progress, evidence timeline, recommendations, approvals, and postmortem.
- Keep the UI evidence-first rather than chatbot-first.

### Deliverables

- Runnable frontend.
- Navigation across all major views.
- API-connected incident experience.

### Done Checklist

- User can open the dashboard and see the checkout incident.
- User can inspect evidence and recommendations.
- User can approve or reject mitigation.
- User can view the generated postmortem.
- UI is visually aligned with the Stitch screens.

## Day 6: Human Approval, Postmortem, And Tests

### Goal

Complete the core incident lifecycle and add test coverage.

### Implementation Tasks

- Finalize approval actions:
  - Approve
  - Reject
  - Request more investigation
- Generate Markdown postmortem from actual incident state.
- Add tests for:
  - Alert ingestion
  - Incident retrieval
  - Workflow execution
  - Evidence ranking
  - Approval decision storage
  - Postmortem generation
- Add basic failure handling:
  - Missing incident ID
  - Invalid approval decision
  - No recommendations available

### Deliverables

- Complete incident lifecycle.
- Markdown postmortem generator.
- pytest test suite.

### Done Checklist

- Approval decision changes incident state.
- Postmortem includes alert, impact, timeline, root cause, mitigation, evidence, and follow-up actions.
- Tests pass locally.
- The app handles common invalid requests cleanly.

## Day 7: Polish And Demo Readiness

### Goal

Make the project portfolio-ready and easy to present.

### Implementation Tasks

- Write a strong `README.md` with:
  - Problem statement
  - Solution summary
  - Architecture
  - Agent workflow
  - Screenshots
  - Setup instructions
  - Demo flow
  - Resume bullet
- Add a demo script:
  - Start app
  - Trigger mock alert
  - Review investigation
  - Approve mitigation
  - Export postmortem
- Add screenshots from the running UI.
- Add project limitations and future improvements.
- Run final verification.

### Deliverables

- Portfolio-ready README.
- Demo script.
- Final screenshots.
- Verified local app.

### Done Checklist

- Full demo can be completed in under five minutes.
- README clearly explains why the project is agentic.
- Project shows RAG, tool use, human-in-the-loop approval, evidence ranking, and postmortem generation.
- Resume bullet is ready to use.

## Final Demo Flow

1. Start the backend and frontend.
2. Open the dashboard.
3. Trigger the mock checkout/payment alert.
4. Watch the agentic workflow gather logs, metrics, deployments, GitHub commits, and runbooks.
5. Review root-cause hypotheses.
6. Review mitigation recommendations.
7. Approve or reject the safest action.
8. Generate and export the postmortem.

## Final Resume Bullet

> Built an agentic incident response platform for e-commerce API outages using FastAPI, LangGraph-style orchestration, RAG over runbooks, log and metric analysis, GitHub/deployment context, human-in-the-loop approvals, and automated postmortem generation.

## Weekly Success Criteria

- The project runs locally end to end.
- The app demonstrates a full incident lifecycle.
- The dashboard is visually aligned with Stitch screens.
- The agent workflow is explainable and evidence-backed.
- The project is strong enough to discuss in AI engineer interviews.

## Notes

- Keep the MVP practical and demoable.
- Do not overbuild production integrations in week one.
- Mocked data is acceptable because the goal is to prove the agentic workflow.
- Real Prometheus, Datadog, GitHub, PostgreSQL, Slack, Kubernetes, and CI/CD integrations can be added after the MVP.
