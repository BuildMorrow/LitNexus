import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        index=True,
    )
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    columns_metadata: Mapped[list] = mapped_column(JSONB, default=list)
    missing_value_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    sample_preview: Mapped[list] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["ResearchProject"] = relationship(back_populates="datasets")
    sessions: Mapped[list["AnalysisSession"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        index=True,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    analysis_goal: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_methods: Mapped[list] = mapped_column(JSONB, default=list)
    selected_method: Mapped[str | None] = mapped_column(String(128))
    generated_code: Mapped[str | None] = mapped_column(Text)
    data_limitations: Mapped[list] = mapped_column(JSONB, default=list)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel), default=RiskLevel.low
    )
    interpretation: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    dataset: Mapped["DatasetProfile"] = relationship(back_populates="sessions")
