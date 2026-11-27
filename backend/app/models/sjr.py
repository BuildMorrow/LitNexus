from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SJRJournal(Base):
    """Offline SCImago Journal Rank (SJR) catalog for fast Scopus Quartile lookup."""

    __tablename__ = "sjr_journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str | None] = mapped_column(String(64), index=True)
    issn: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    quartile: Mapped[str] = mapped_column(String(8), nullable=False)
    sjr_score: Mapped[float | None] = mapped_column(Float)
    h_index: Mapped[int | None] = mapped_column(Integer)
    areas: Mapped[str | None] = mapped_column(Text)
