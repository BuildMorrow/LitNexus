"""Add local_pdf_path on papers, workspace_messages table, and vector index.

Revision ID: 0003_sprint_d_rag_workspace
Revises: 0002_sprint_b_setup_snowball_sjr
Create Date: 2026-11-27 12:35:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_sprint_d_rag_workspace"
down_revision: str | Sequence[str] | None = "0002_sprint_b_setup_snowball_sjr"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("papers", sa.Column("local_pdf_path", sa.Text(), nullable=True))

    op.create_table(
        "workspace_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("guardrail", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workspace_messages_project_id", "workspace_messages", ["project_id"])


def downgrade() -> None:
    op.drop_table("workspace_messages")
    op.drop_column("papers", "local_pdf_path")
