from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260611_0003"
down_revision = "20260610_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mitigation_executions",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("recommendation_id", sa.String(length=120), nullable=False),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("before_metrics", sa.JSON(), nullable=False),
        sa.Column("after_metrics", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_mitigation_executions_incident_id",
        "mitigation_executions",
        ["incident_id"],
    )

    op.create_table(
        "recovery_checks",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("incident_id", sa.String(length=120), nullable=False),
        sa.Column("execution_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observations", sa.JSON(), nullable=False),
        sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("measured_metrics", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_recovery_checks_incident_id",
        "recovery_checks",
        ["incident_id"],
    )

    op.add_column(
        "postmortems",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
    )
    op.add_column(
        "postmortems",
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("postmortems", "finalized_at")
    op.drop_column("postmortems", "status")
    op.drop_index("ix_recovery_checks_incident_id", table_name="recovery_checks")
    op.drop_table("recovery_checks")
    op.drop_index(
        "ix_mitigation_executions_incident_id",
        table_name="mitigation_executions",
    )
    op.drop_table("mitigation_executions")
