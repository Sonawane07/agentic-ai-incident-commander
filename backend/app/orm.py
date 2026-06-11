from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    service: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    affected_service: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    alert_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_reference: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)


class HypothesisRecord(Base):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    contradicting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    unknowns: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class MitigationRecommendationRecord(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    hypothesis_id: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)


class ApprovalDecisionRecord(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    decision: Mapped[str] = mapped_column(String(80), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class MitigationExecutionRecord(Base):
    __tablename__ = "mitigation_executions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    before_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    after_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class RecoveryCheckRecord(Base):
    __tablename__ = "recovery_checks"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    checked_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    observations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    thresholds: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    measured_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class PostmortemRecord(Base):
    __tablename__ = "postmortems"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    root_cause_summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_actions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    finalized_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TimelineEventRecord(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(120), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class AgentTraceRecord(Base):
    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)


class RunbookChunkRecord(Base):
    __tablename__ = "runbook_chunks"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    runbook_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    section_title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    service: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
