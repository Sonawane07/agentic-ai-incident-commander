from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260610_0002"
down_revision = "20260609_0001"
branch_labels = None
depends_on = None

EMBEDDING_DIMENSION = 384


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.add_column(
            "runbook_chunks",
            sa.Column("embedding_vector", sa.Text(), nullable=True),
        )
        op.execute(
            f"ALTER TABLE runbook_chunks ALTER COLUMN embedding_vector TYPE vector({EMBEDDING_DIMENSION}) "
            "USING embedding_vector::vector"
        )
        op.create_index(
            "ix_runbook_chunks_embedding_vector",
            "runbook_chunks",
            ["embedding_vector"],
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding_vector": "vector_cosine_ops"},
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_runbook_chunks_embedding_vector", table_name="runbook_chunks")
        op.drop_column("runbook_chunks", "embedding_vector")
