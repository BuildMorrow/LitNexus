import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(128))
    research_question: Mapped[str] = mapped_column(Text, nullable=False)

    # PICO Framework & PRISMA Criteria
    pico_framework: Mapped[dict] = mapped_column(JSONB, default=dict)
    inclusion_criteria: Mapped[list] = mapped_column(JSONB, default=list)
    exclusion_criteria: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    owner: Mapped["User"] = relationship(back_populates="projects")
    papers: Mapped[list["Paper"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    conflict_edges: Mapped[list["ConflictEdge"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    research_gaps: Mapped[list["ResearchGap"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
