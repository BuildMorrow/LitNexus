"""Verify Alembic migration script discovery and SQLAlchemy metadata alignment."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

import app.models  # noqa: F401
from app.core.database import Base


def test_alembic_initial_revision_and_metadata_tables():
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert heads == ["0001_initial_schema"]

    expected_tables = {
        "users",
        "research_projects",
        "papers",
        "paper_chunks",
        "paper_claims",
        "conflict_edges",
        "research_gaps",
        "dataset_profiles",
        "analysis_sessions",
    }
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
