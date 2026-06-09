# Roadmap

## 1. Roadmap Summary

The MVP should be built in six phases, moving from documentation and mocked data to a polished demo with LangGraph orchestration, runbook RAG, approval flow, postmortem generation, evaluations, and portfolio-ready presentation.

## Phase 1: Documentation And Mocked Data Model

Goal:

- Establish the product scope, incident scenario, core data objects, and seeded demo data.

Deliverables:

- PRD, architecture, data flow, user flow, and roadmap documents.
- Mock alert payloads for checkout latency and payment failures.
- Mock metrics for latency, error rate, throughput, DB pool usage, CPU, and memory.
- Mock logs containing payment timeout and database pool exhaustion events.
- Mock deployment and GitHub commit records.
- Runbook Markdown files for checkout latency, payment provider timeout, DB pool saturation, and rollback.

Acceptance criteria:

- Demo incident can be explained entirely from seeded data.
- Data fixtures support at least one strong root-cause path and one alternative hypothesis.

## Phase 2: FastAPI Backend And Incident Store

Goal:

- Build the backend foundation for incident creation, storage, retrieval, and timeline tracking.

Deliverables:

- FastAPI service.
- PostgreSQL schema for alerts, incidents, evidence, hypotheses, recommendations, approvals, and postmortems.
- API endpoints for alert ingestion, incident listing, incident detail, evidence timeline, recommendations, approvals, and postmortem retrieval.
- Seed script for mock incidents and observability data.

Acceptance criteria:

- `POST /alerts` creates an incident.
- `GET /incidents/{incident_id}` returns incident details.
- Evidence can be persisted and retrieved by incident.

## Phase 3: LangGraph Multi-Agent Investigation Workflow

Goal:

- Implement the agentic workflow that investigates an incident using specialist agents.

Deliverables:

- LangGraph state definition for incident investigation.
- Alert Intake Agent.
- Metrics Agent.
- Logs Agent.
- GitHub/Deploy Agent.
- Root Cause Agent.
- Mitigation Agent.
- Approval pause/resume node.
- Basic trace logging for each agent step.

Acceptance criteria:

- A mock alert triggers a full investigation workflow.
- The workflow stores evidence and hypotheses.
- The workflow pauses when human approval is required.

## Phase 4: RAG Over Runbooks And Evidence Ranking

Goal:

- Add runbook retrieval and improve quality of evidence-backed reasoning.

Deliverables:

- Runbook ingestion pipeline.
- Qdrant or Chroma vector index.
- Runbook RAG Agent.
- Evidence ranking by relevance, time proximity, affected service, and source agreement.
- Cited runbook snippets in root-cause and mitigation outputs.

Acceptance criteria:

- The agent retrieves relevant runbook sections for checkout latency and payment failures.
- Root-cause hypotheses cite runbook and operational evidence.
- Mitigation recommendations include evidence references.

## Phase 5: React Dashboard And Approval Flow

Goal:

- Build the user-facing incident response experience.

Deliverables:

- Incident list view.
- Active investigation view.
- Evidence timeline.
- Root-cause hypothesis panel.
- Mitigation recommendation panel.
- Approval modal.
- Postmortem view.

Acceptance criteria:

- User can trigger or open a mock incident.
- User can inspect evidence and recommendations.
- User can approve, reject, or request more investigation.
- Approval decision is stored and visible in the timeline.

## Phase 6: Postmortem Generation, Evals, Tracing, And Portfolio Polish

Goal:

- Make the project credible, measurable, and portfolio-ready.

Deliverables:

- Postmortem Agent.
- Markdown postmortem export.
- Evaluation scenarios for root-cause quality and recommendation quality.
- Trace dashboard or trace log view.
- README with problem statement, architecture, screenshots, demo flow, and resume bullet.
- Demo video script.

Acceptance criteria:

- Postmortem is generated from actual incident state and evidence.
- Eval scenarios can be run locally.
- README explains why the project is agentic and production-relevant.
- Demo can be completed in under five minutes.

## Future Upgrades

- Real Prometheus integration.
- Real Grafana or Datadog alert ingestion.
- Real GitHub PR/commit integration.
- Slack alert and incident updates.
- CI/CD integration.
- Authentication and role-based access control.
- Kubernetes deployment.
- Real rollback integration with approval and dry-run mode.
- OpenTelemetry trace ingestion.
- Multi-service dependency graph.
- Learning loop from resolved incidents.

## Recommended Build Order

1. Build seeded mock data first.
2. Build backend incident APIs.
3. Add LangGraph workflow with mocked tools.
4. Add RAG over runbooks.
5. Build dashboard.
6. Add postmortem, evals, traces, and portfolio polish.

This order keeps the project demoable early while gradually adding deeper agentic behavior.
