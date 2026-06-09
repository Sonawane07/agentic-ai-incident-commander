from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IncidentStatus(StrEnum):
    NEW = "new"
    INVESTIGATING = "investigating"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    MITIGATION_RECORDED = "mitigation_recorded"
    CLOSED = "closed"


class EvidenceSourceType(StrEnum):
    METRIC = "metric"
    LOG = "log"
    DEPLOYMENT = "deployment"
    GITHUB_COMMIT = "github_commit"
    RUNBOOK = "runbook"
    TRACE = "trace"
    HUMAN_DECISION = "human_decision"


class MitigationActionType(StrEnum):
    ROLLBACK = "rollback"
    SCALE_RESOURCE = "scale_resource"
    DISABLE_FEATURE_FLAG = "disable_feature_flag"
    PROVIDER_FAILOVER = "provider_failover"
    MONITOR_ONLY = "monitor_only"


class ApprovalDecisionValue(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MORE_INVESTIGATION_REQUIRED = "more_investigation_required"


class Alert(BaseModel):
    id: str
    source: str
    service: str
    severity: str
    metric_name: str
    metric_value: float
    threshold: float
    started_at: datetime
    description: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    id: str
    title: str
    status: IncidentStatus
    severity: str
    affected_service: str
    created_at: datetime
    updated_at: datetime
    current_stage: str
    summary: str
    alert_id: str


class Evidence(BaseModel):
    id: str
    incident_id: str
    source_type: EvidenceSourceType
    source_name: str
    timestamp: datetime
    summary: str
    raw_reference: str
    confidence: float = Field(ge=0, le=1)
    relevance_score: float = Field(ge=0, le=1)


class RunbookChunk(BaseModel):
    id: str
    runbook_title: str
    section_title: str
    content: str
    embedding: list[float] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    service: str
    updated_at: datetime


class Hypothesis(BaseModel):
    id: str
    incident_id: str
    title: str
    description: str
    confidence: float = Field(ge=0, le=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class MitigationRecommendation(BaseModel):
    id: str
    incident_id: str
    hypothesis_id: str
    action_type: MitigationActionType
    title: str
    description: str
    risk_level: str
    confidence: float = Field(ge=0, le=1)
    requires_approval: bool
    expected_impact: str


class ApprovalDecision(BaseModel):
    id: str
    incident_id: str
    recommendation_id: str
    decision: ApprovalDecisionValue
    decided_by: str
    reason: str
    created_at: datetime


class Postmortem(BaseModel):
    id: str
    incident_id: str
    markdown: str
    generated_at: datetime
    root_cause_summary: str
    impact_summary: str
    follow_up_actions: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    id: str
    incident_id: str
    stage: str
    actor: str
    message: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    id: str
    incident_id: str
    agent_name: str
    input_summary: str
    output_summary: str
    started_at: datetime
    completed_at: datetime
    status: str = "completed"


class MetricSample(BaseModel):
    timestamp: datetime
    value: float


class MetricSeries(BaseModel):
    service: str
    metric_name: str
    unit: str
    samples: list[MetricSample]


class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    service: str
    level: str
    message: str
    error_code: str | None = None
    trace_id: str | None = None


class DeploymentRecord(BaseModel):
    id: str
    service: str
    version: str
    environment: str
    deployed_at: datetime
    status: str
    summary: str
    commit_ids: list[str] = Field(default_factory=list)


class GitHubCommit(BaseModel):
    id: str
    sha: str
    author: str
    committed_at: datetime
    message: str
    changed_files: list[str]
    risk_notes: list[str] = Field(default_factory=list)


class DemoData(BaseModel):
    alerts: list[Alert]
    incidents: list[Incident]
    metrics: list[MetricSeries]
    logs: list[LogEntry]
    deployments: list[DeploymentRecord]
    github_commits: list[GitHubCommit]
    runbook_chunks: list[RunbookChunk]
