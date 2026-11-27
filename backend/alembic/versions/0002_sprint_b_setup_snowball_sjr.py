"""Add search_queries, sjr_journals, and paper provenance columns.

Revision ID: 0002_sprint_b_setup_snowball_sjr
Revises: 0001_initial_schema
Create Date: 2026-11-27 12:15:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_sprint_b_setup_snowball_sjr"
down_revision: str | Sequence[str] | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "papers",
        sa.Column("discovery_source", sa.String(length=32), nullable=False, server_default="keyword"),
    )
    op.add_column(
        "papers",
        sa.Column("seed_distance", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "search_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_string", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="keyword"),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_search_queries_project_id", "search_queries", ["project_id"])

    op.create_table(
        "sjr_journals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("issn", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("quartile", sa.String(length=8), nullable=False),
        sa.Column("sjr_score", sa.Float(), nullable=True),
        sa.Column("h_index", sa.Integer(), nullable=True),
        sa.Column("areas", sa.Text(), nullable=True),
    )
    op.create_index("ix_sjr_journals_source_id", "sjr_journals", ["source_id"])
    op.create_index("ix_sjr_journals_issn", "sjr_journals", ["issn"])
    op.create_index("ix_sjr_journals_normalized_title", "sjr_journals", ["normalized_title"])


def downgrade() -> None:
    op.drop_table("sjr_journals")
    op.drop_table("search_queries")
    op.drop_column("papers", "seed_distance")
    op.drop_column("papers", "discovery_source")
