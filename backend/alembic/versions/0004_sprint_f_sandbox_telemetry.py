"""Add raw_csv_text on dataset_profiles and llm_usage_logs telemetry table.

Revision ID: 0004_sprint_f_sandbox_telemetry
Revises: 0003_sprint_d_rag_workspace
Create Date: 2026-11-27 12:55:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_sprint_f_sandbox_telemetry"
down_revision: str | Sequence[str] | None = "0003_sprint_d_rag_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dataset_profiles", sa.Column("raw_csv_text", sa.Text(), nullable=True))

    op.create_table(
        "llm_usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("task_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_llm_usage_logs_project_id", "llm_usage_logs", ["project_id"])
    op.create_index("ix_llm_usage_logs_task_name", "llm_usage_logs", ["task_name"])


def downgrade() -> None:
    op.drop_table("llm_usage_logs")
    op.drop_column("dataset_profiles", "raw_csv_text")
