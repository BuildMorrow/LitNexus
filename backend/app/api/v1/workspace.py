import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_project
from app.core.database import get_db
from app.models.project import ResearchProject
from app.models.workspace import WorkspaceMessage
from app.services.rag_service import answer_workspace_question

router = APIRouter(prefix="/projects/{project_id}/workspace", tags=["workspace"])


class WorkspaceChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    paper_ids: list[uuid.UUID] | None = None


class WorkspaceMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    guardrail: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


@router.get("/messages", response_model=list[WorkspaceMessageOut])
async def list_workspace_messages(
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(WorkspaceMessage)
        .where(WorkspaceMessage.project_id == project.id)
        .order_by(WorkspaceMessage.created_at.asc())
        .limit(100)
    )
    return list(res.scalars().all())


@router.post("/chat", response_model=WorkspaceMessageOut)
async def chat_with_workspace(
    payload: WorkspaceChatRequest,
    project: ResearchProject = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Run guarded Hybrid RAG Q&A strictly scoped to the owned project and selected papers."""
    try:
        answer, citations, guardrail = await answer_workspace_question(
            db,
            project_id=project.id,
            question=payload.question,
            paper_ids=payload.paper_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG chat failed: {exc}") from exc

    user_msg = WorkspaceMessage(
        project_id=project.id,
        role="user",
        content=payload.question,
        citations=[],
        guardrail={},
    )
    assistant_msg = WorkspaceMessage(
        project_id=project.id,
        role="assistant",
        content=answer,
        citations=citations,
        guardrail=guardrail.model_dump(),
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    return assistant_msg
