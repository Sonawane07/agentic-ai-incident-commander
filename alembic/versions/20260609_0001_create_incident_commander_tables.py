from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260609_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("service", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("metric_name", sa.String(length=120), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_alerts_service", "alerts", ["service"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("affected_service", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_stage", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("alert_id", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_affected_service", "incidents", ["affected_service"])
    op.create_index("ix_incidents_alert_id", "incidents", ["alert_id"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("raw_reference", sa.String(length=500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
    )
    op.create_index("ix_evidence_incident_id", "evidence", ["incident_id"])

    op.create_table(
        "hypotheses",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("supporting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("contradicting_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("unknowns", sa.JSON(), nullable=False),
    )
    op.create_index("ix_hypotheses_incident_id", "hypotheses", ["incident_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("hypothesis_id", sa.String(length=120), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("expected_impact", sa.Text(), nullable=False),
    )
    op.create_index("ix_recommendations_incident_id", "recommendations", ["incident_id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("recommendation_id", sa.String(length=120), nullable=False),
        sa.Column("decision", sa.String(length=80), nullable=False),
        sa.Column("decided_by", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approvals_incident_id", "approvals", ["incident_id"])

    op.create_table(
        "postmortems",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False, unique=True),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("root_cause_summary", sa.Text(), nullable=False),
        sa.Column("impact_summary", sa.Text(), nullable=False),
        sa.Column("follow_up_actions", sa.JSON(), nullable=False),
    )
    op.create_index("ix_postmortems_incident_id", "postmortems", ["incident_id"])

    op.create_table(
        "timeline_events",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("stage", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_timeline_events_incident_id", "timeline_events", ["incident_id"])

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
    )
    op.create_index("ix_agent_traces_incident_id", "agent_traces", ["incident_id"])

    op.create_table(
        "runbook_chunks",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("runbook_title", sa.String(length=255), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("service", sa.String(length=120), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runbook_chunks_runbook_title", "runbook_chunks", ["runbook_title"])
    op.create_index("ix_runbook_chunks_service", "runbook_chunks", ["service"])


def downgrade() -> None:
    op.drop_index("ix_runbook_chunks_service", table_name="runbook_chunks")
    op.drop_index("ix_runbook_chunks_runbook_title", table_name="runbook_chunks")
    op.drop_table("runbook_chunks")
    op.drop_index("ix_agent_traces_incident_id", table_name="agent_traces")
    op.drop_table("agent_traces")
    op.drop_index("ix_timeline_events_incident_id", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_index("ix_postmortems_incident_id", table_name="postmortems")
    op.drop_table("postmortems")
    op.drop_index("ix_approvals_incident_id", table_name="approvals")
    op.drop_table("approvals")
    op.drop_index("ix_recommendations_incident_id", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("ix_hypotheses_incident_id", table_name="hypotheses")
    op.drop_table("hypotheses")
    op.drop_index("ix_evidence_incident_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_incidents_alert_id", table_name="incidents")
    op.drop_index("ix_incidents_affected_service", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("ix_alerts_service", table_name="alerts")
    op.drop_table("alerts")
