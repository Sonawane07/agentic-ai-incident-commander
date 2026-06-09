# Data Flow

## 1. Data Flow Summary

The system receives a checkout/payment API alert, creates an incident, and starts a LangGraph investigation. Specialist agents gather evidence from mocked logs, metrics, deployments, GitHub commits, and runbooks. The workflow produces a root-cause hypothesis, ranks mitigation options, captures human approval, and generates a postmortem.

## 2. Full Incident Lifecycle

```mermaid
flowchart TD
    A["Mock Alert Received"] --> B["Create Incident"]
    B --> C["Start LangGraph Workflow"]
    C --> D["Normalize Alert Context"]
    D --> E1["Query Metrics"]
    D --> E2["Search Logs"]
    D --> E3["Check Deployments + GitHub Commits"]
    D --> E4["Retrieve Runbooks via RAG"]
    E1 --> F["Store Evidence"]
    E2 --> F
    E3 --> F
    E4 --> F
    F --> G["Generate Root-Cause Hypotheses"]
    G --> H["Rank Mitigation Recommendations"]
    H --> I["Request Human Approval"]
    I --> J{"Decision"}
    J -->|Approve| K["Mark Mitigation Executed in Demo"]
    J -->|Reject| L["Record Rejection Reason"]
    J -->|Need More Evidence| E1
    K --> M["Generate Postmortem"]
    L --> M
    M --> N["Export Markdown Report"]
```

## 3. Sequence Flow

```mermaid
sequenceDiagram
    participant Alert as Mock Alert Source
    participant API as FastAPI Backend
    participant Graph as LangGraph Workflow
    participant Metrics as Metrics Agent
    participant Logs as Logs Agent
    participant GitHub as GitHub/Deploy Agent
    participant RAG as Runbook RAG Agent
    participant DB as PostgreSQL
    participant UI as React Dashboard
    participant User as On-call Engineer

    Alert->>API: POST /alerts
    API->>DB: Create incident
    API->>Graph: Start investigation
    Graph->>Metrics: Query latency/error/db metrics
    Graph->>Logs: Search checkout/payment logs
    Graph->>GitHub: Fetch recent deploys and commits
    Graph->>RAG: Retrieve relevant runbooks
    Metrics->>DB: Store metric evidence
    Logs->>DB: Store log evidence
    GitHub->>DB: Store deploy evidence
    RAG->>DB: Store runbook evidence
    Graph->>DB: Store hypotheses and recommendations
    UI->>API: Fetch incident status
    API->>UI: Return timeline and recommendations
    User->>UI: Approve or reject mitigation
    UI->>API: POST approval decision
    API->>Graph: Resume workflow
    Graph->>DB: Store postmortem
    UI->>API: Fetch postmortem
```

## 4. Main Data Objects

### Alert

Represents the incoming incident trigger.

Fields:

- `id`
- `source`
- `service`
- `severity`
- `metric_name`
- `metric_value`
- `threshold`
- `started_at`
- `description`
- `raw_payload`

Example:

```json
{
  "source": "mock_datadog",
  "service": "checkout-api",
  "severity": "critical",
  "metric_name": "p95_latency_ms",
  "metric_value": 2400,
  "threshold": 800,
  "description": "Checkout p95 latency exceeded threshold and payment failures increased."
}
```

### Incident

Tracks the full lifecycle of an investigation.

Fields:

- `id`
- `title`
- `status`
- `severity`
- `affected_service`
- `created_at`
- `updated_at`
- `current_stage`
- `summary`

Allowed MVP statuses:

- `new`
- `investigating`
- `waiting_for_approval`
- `mitigation_recorded`
- `closed`

### Evidence

Stores observations collected by agents.

Fields:

- `id`
- `incident_id`
- `source_type`
- `source_name`
- `timestamp`
- `summary`
- `raw_reference`
- `confidence`
- `relevance_score`

Source types:

- `metric`
- `log`
- `deployment`
- `github_commit`
- `runbook`
- `trace`
- `human_decision`

### RunbookChunk

Represents indexed runbook content in the vector store.

Fields:

- `id`
- `runbook_title`
- `section_title`
- `content`
- `embedding`
- `tags`
- `service`
- `updated_at`

### Hypothesis

Represents an evidence-backed root-cause theory.

Fields:

- `id`
- `incident_id`
- `title`
- `description`
- `confidence`
- `supporting_evidence_ids`
- `contradicting_evidence_ids`
- `unknowns`

Example:

```json
{
  "title": "Database connection pool saturation after checkout deployment",
  "confidence": 0.82,
  "description": "Checkout latency increased shortly after deployment v1.42.0, while DB pool usage reached 98% and logs show DB_POOL_EXHAUSTED errors."
}
```

### MitigationRecommendation

Represents a proposed response.

Fields:

- `id`
- `incident_id`
- `hypothesis_id`
- `action_type`
- `title`
- `description`
- `risk_level`
- `confidence`
- `requires_approval`
- `expected_impact`

Action types:

- `rollback`
- `scale_resource`
- `disable_feature_flag`
- `provider_failover`
- `monitor_only`

### ApprovalDecision

Captures human-in-the-loop control.

Fields:

- `id`
- `incident_id`
- `recommendation_id`
- `decision`
- `decided_by`
- `reason`
- `created_at`

Allowed decisions:

- `approved`
- `rejected`
- `more_investigation_required`

### Postmortem

Represents the generated incident report.

Fields:

- `id`
- `incident_id`
- `markdown`
- `generated_at`
- `root_cause_summary`
- `impact_summary`
- `follow_up_actions`

## 5. Evidence Ranking Logic

The MVP should rank evidence by:

- Time proximity to the alert.
- Match to affected service.
- Severity of observed anomaly.
- Agreement with other evidence sources.
- Runbook relevance score.

The root-cause agent should not rely on a single evidence source when multiple sources are available.

## 6. Postmortem Data Inputs

The postmortem agent uses:

- Original alert
- Incident status timeline
- Key evidence summaries
- Final root-cause hypothesis
- Mitigation recommendations
- Human approval decision
- Follow-up action list

The generated postmortem must be readable as a standalone Markdown report.
