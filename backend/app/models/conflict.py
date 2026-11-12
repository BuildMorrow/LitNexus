import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EdgeRelationType(str, enum.Enum):
    contradicts = "contradicts"
    supports = "supports"
    refines = "refines"
    assumption_mismatch = "assumption_mismatch"


class PaperClaim(Base):
    """Structured scientific claim extracted from an included paper."""

    __tablename__ = "paper_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), index=True
    )

    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str | None] = mapped_column(String(255))
    dataset: Mapped[str | None] = mapped_column(String(255))
    metric_summary: Mapped[str | None] = mapped_column(String(255))
    assumptions: Mapped[list] = mapped_column(JSONB, default=list)
    evidence_quote: Mapped[str | None] = mapped_column(Text)

    paper: Mapped["Paper"] = relationship(back_populates="claims")


class ConflictEdge(Base):
    """Cross-paper comparison edge produced by the Cross-Examiner Agent."""

    __tablename__ = "conflict_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        index=True,
    )
    source_claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_claims.id", ondelete="CASCADE")
    )
    target_claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paper_claims.id", ondelete="CASCADE")
    )

    relation_type: Mapped[EdgeRelationType] = mapped_column(
        Enum(EdgeRelationType), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    debate_summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_hypothesis: Mapped[str | None] = mapped_column(Text)

    project: Mapped["ResearchProject"] = relationship(back_populates="conflict_edges")


class ResearchGap(Base):
    """Actionable research gap synthesized from cross-paper conflicts."""

    __tablename__ = "research_gaps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_conflict_ids: Mapped[list] = mapped_column(JSONB, default=list)
    suggested_direction: Mapped[str | None] = mapped_column(Text)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["ResearchProject"] = relationship(back_populates="research_gaps")
