from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.main import app
from app.schemas.project import ProjectCreate, UserCreate, UserLogin


def test_app_registers_all_sprint_routes_and_openapi_schema():
    """Verify FastAPI app imports cleanly, generates valid OpenAPI schema, and registers all Sprint A-F routes."""
    openapi_schema = app.openapi()
    assert openapi_schema["info"]["title"]
    registered_paths = set(openapi_schema.get("paths", {}).keys())

    expected_routes = {
        "/api/v1/health",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/projects/assist/scope-optimizer",
        "/api/v1/projects/assist/criteria-generator",
        "/api/v1/projects/assist/pico-query",
        "/api/v1/projects/{project_id}/papers",
        "/api/v1/projects/{project_id}/search",
        "/api/v1/projects/{project_id}/search/snowball",
        "/api/v1/projects/{project_id}/search/history",
        "/api/v1/projects/{project_id}/papers/{paper_id}/ingest-pdf",
        "/api/v1/projects/{project_id}/papers/{paper_id}/upload-pdf",
        "/api/v1/projects/{project_id}/papers/{paper_id}/pdf-highlight",
        "/api/v1/projects/{project_id}/screening/quality-gate",
        "/api/v1/projects/{project_id}/screening/papers/{paper_id}/label",
        "/api/v1/projects/{project_id}/screening/papers/{paper_id}/hitl-override",
        "/api/v1/projects/{project_id}/screening/run-active-learning",
        "/api/v1/projects/{project_id}/screening/auto-label-uncertain",
        "/api/v1/projects/{project_id}/screening/dual-peer-screen",
        "/api/v1/projects/{project_id}/conflicts",
        "/api/v1/projects/{project_id}/conflicts/analyze",
        "/api/v1/projects/{project_id}/conflicts/comparative-matrix",
        "/api/v1/projects/{project_id}/conflicts/kpi-metrics",
        "/api/v1/projects/{project_id}/conflicts/graph",
        "/api/v1/projects/{project_id}/conflicts/export-draft",
        "/api/v1/projects/{project_id}/conflicts/export-xlsx",
        "/api/v1/projects/{project_id}/conflicts/usage-observability",
        "/api/v1/projects/{project_id}/analysis/datasets",
        "/api/v1/projects/{project_id}/analysis/datasets/upload-file",
        "/api/v1/projects/{project_id}/analysis/datasets/{dataset_id}/advise",
        "/api/v1/projects/{project_id}/analysis/datasets/{dataset_id}/execute",
        "/api/v1/projects/{project_id}/workspace/messages",
        "/api/v1/projects/{project_id}/workspace/chat",
    }

    missing = expected_routes - registered_paths
    assert not missing, f"Missing expected API routes: {missing}"


def test_user_and_project_pydantic_schemas():
    """Verify EmailStr and project creation schemas validate properly."""
    user = UserCreate(
        email="researcher@litnexus.ai",
        password="securePassword123",
        full_name="Dr. LitNexus",
    )
    assert user.email == "researcher@litnexus.ai"

    login = UserLogin(email="researcher@litnexus.ai", password="securePassword123")
    assert login.email == "researcher@litnexus.ai"

    project = ProjectCreate(
        title="Systematic Review on Agentic RAG",
        research_question="How do multi-agent verification pipelines reduce citation hallucination?",
        inclusion_criteria=["Peer-reviewed empirical studies (2021-2026) reporting citation precision"],
        exclusion_criteria=["Non-peer-reviewed blog posts or tutorials without benchmarks"],
    )
    assert "Agentic RAG" in project.title
    assert len(project.inclusion_criteria) == 1


@pytest.mark.asyncio
async def test_health_endpoint_responds_ok():
    """Smoke test /api/v1/health endpoint using ASGI transport without requiring a live DB."""
    with patch("app.main.init_db", new=AsyncMock()):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
            payload = response.json()
            assert payload["status"] == "ok"
