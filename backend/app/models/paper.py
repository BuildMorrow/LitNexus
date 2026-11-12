import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScreeningStatus(str, enum.Enum):
    unscreened = "unscreened"
    included = "included"
    excluded = "excluded"
    uncertain = "uncertain"


class ScreeningSource(str, enum.Enum):
    none = "none"
    human = "human"
    llm = "llm"
    active_learning = "active_learning"


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        index=True,
    )

    # Identifiers & Metadata
    doi: Mapped[str | None] = mapped_column(String(255), index=True)
    openalex_id: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list] = mapped_column(JSONB, default=list)
    journal: Mapped[str | None] = mapped_column(String(255))
    issn: Mapped[str | None] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    abstract: Mapped[str | None] = mapped_column(Text)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    pdf_url: Mapped[str | None] = mapped_column(Text)

    # Journal Verification
    scopus_quartile: Mapped[str | None] = mapped_column(String(16))  # Q1, Q2, Q3, Q4

    # Stage 1: Active Learning Hybrid Screening
    screening_status: Mapped[ScreeningStatus] = mapped_column(
        Enum(ScreeningStatus), default=ScreeningStatus.unscreened, index=True
    )
    screening_source: Mapped[ScreeningSource] = mapped_column(
        Enum(ScreeningSource), default=ScreeningSource.none
    )
    al_inclusion_prob: Mapped[float | None] = mapped_column(Float)
    al_uncertainty_score: Mapped[float | None] = mapped_column(Float)
    screening_rationale: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["ResearchProject"] = relationship(back_populates="papers")
    chunks: Mapped[list["PaperChunk"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    claims: Mapped[list["PaperClaim"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
