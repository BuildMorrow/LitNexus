"""Initial baseline schema for LitNexus PostgreSQL + pgvector.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-27 12:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "research_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("pico_framework", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("inclusion_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("exclusion_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_projects_owner_id", "research_projects", ["owner_id"])

    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doi", sa.String(length=255), nullable=True),
        sa.Column("openalex_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("journal", sa.String(length=255), nullable=True),
        sa.Column("issn", sa.String(length=64), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("scopus_quartile", sa.String(length=16), nullable=True),
        sa.Column(
            "screening_status",
            sa.Enum("unscreened", "included", "excluded", "uncertain", name="screeningstatus"),
            nullable=False,
        ),
        sa.Column(
            "screening_source",
            sa.Enum("none", "human", "llm", "active_learning", name="screeningsource"),
            nullable=False,
        ),
        sa.Column("al_inclusion_prob", sa.Float(), nullable=True),
        sa.Column("al_uncertainty_score", sa.Float(), nullable=True),
        sa.Column("screening_rationale", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_papers_project_id", "papers", ["project_id"])
    op.create_index("ix_papers_doi", "papers", ["doi"])
    op.create_index("ix_papers_openalex_id", "papers", ["openalex_id"])
    op.create_index("ix_papers_screening_status", "papers", ["screening_status"])

    op.create_table(
        "paper_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_paper_chunks_paper_id", "paper_chunks", ["paper_id"])

    op.create_table(
        "paper_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("methodology", sa.String(length=255), nullable=True),
        sa.Column("dataset", sa.String(length=255), nullable=True),
        sa.Column("metric_summary", sa.String(length=255), nullable=True),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_paper_claims_paper_id", "paper_claims", ["paper_id"])

    op.create_table(
        "conflict_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paper_claims.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paper_claims.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "relation_type",
            sa.Enum(
                "contradicts",
                "supports",
                "refines",
                "assumption_mismatch",
                name="edgerelationtype",
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("debate_summary", sa.Text(), nullable=False),
        sa.Column("root_cause_hypothesis", sa.Text(), nullable=True),
    )
    op.create_index("ix_conflict_edges_project_id", "conflict_edges", ["project_id"])
    op.create_index("ix_conflict_edges_relation_type", "conflict_edges", ["relation_type"])

    op.create_table(
        "research_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "supporting_conflict_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("suggested_direction", sa.Text(), nullable=True),
        sa.Column("novelty_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_gaps_project_id", "research_gaps", ["project_id"])

    op.create_table(
        "dataset_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("columns_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_value_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sample_preview", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dataset_profiles_project_id", "dataset_profiles", ["project_id"])

    op.create_table(
        "analysis_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("analysis_goal", sa.Text(), nullable=False),
        sa.Column("recommended_methods", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("selected_method", sa.String(length=128), nullable=True),
        sa.Column("generated_code", sa.Text(), nullable=True),
        sa.Column("data_limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", name="risklevel"),
            nullable=False,
        ),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_sessions_project_id", "analysis_sessions", ["project_id"])
    op.create_index("ix_analysis_sessions_dataset_id", "analysis_sessions", ["dataset_id"])


def downgrade() -> None:
    op.drop_table("analysis_sessions")
    op.drop_table("dataset_profiles")
    op.drop_table("research_gaps")
    op.drop_table("conflict_edges")
    op.drop_table("paper_claims")
    op.drop_table("paper_chunks")
    op.drop_table("papers")
    op.drop_table("research_projects")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS edgerelationtype")
    op.execute("DROP TYPE IF EXISTS screeningsource")
    op.execute("DROP TYPE IF EXISTS screeningstatus")
