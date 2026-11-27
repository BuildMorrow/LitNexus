"""SCImago Journal Rank (SJR) lookup service.

Supports fast lookup from:
1. PostgreSQL `sjr_journals` table (when imported via scripts/import_sjr.py),
2. Optional local SCImago CSV catalog (`backend/data/scimagojr.csv`), and
3. Built-in high-impact journal seed fallback.
"""

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sjr import SJRJournal

# Standard reference seed of prominent academic journals across CS, AI, Medical, and Engineering
_KNOWN_JOURNALS: dict[str, tuple[str, float]] = {
    "IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE": ("Q1", 4.85),
    "JOURNAL OF MACHINE LEARNING RESEARCH": ("Q1", 3.20),
    "IEEE TRANSACTIONS ON NEURAL NETWORKS AND LEARNING SYSTEMS": ("Q1", 2.95),
    "ARTIFICIAL INTELLIGENCE": ("Q1", 2.65),
    "NEURAL NETWORKS": ("Q1", 2.10),
    "PATTERN RECOGNITION": ("Q1", 2.05),
    "IEEE TRANSACTIONS ON BIOMEDICAL ENGINEERING": ("Q1", 1.85),
    "NATURE BIOTECHNOLOGY": ("Q1", 15.2),
    "NATURE MEDICINE": ("Q1", 14.1),
    "NATURE MACHINE INTELLIGENCE": ("Q1", 6.75),
    "LANCET DIGITAL HEALTH": ("Q1", 8.90),
    "THE LANCET": ("Q1", 16.5),
    "NEW ENGLAND JOURNAL OF MEDICINE": ("Q1", 18.2),
    "PLOS ONE": ("Q2", 0.85),
    "SCIENTIFIC REPORTS": ("Q1", 1.15),
    "IEEE ACCESS": ("Q2", 0.92),
    "SENSORS": ("Q2", 0.88),
    "APPLIED SCIENCES": ("Q2", 0.65),
    "COMPUTERS IN BIOLOGY AND MEDICINE": ("Q1", 1.65),
    "BIOMEDICAL SIGNAL PROCESSING AND CONTROL": ("Q1", 1.45),
    "EXPERT SYSTEMS WITH APPLICATIONS": ("Q1", 2.15),
    "KNOWLEDGE-BASED SYSTEMS": ("Q1", 2.05),
}

_KNOWN_ISSNS: dict[str, tuple[str, float]] = {
    "0162-8828": ("Q1", 4.85),
    "1532-4435": ("Q1", 3.20),
    "2162-237X": ("Q1", 2.95),
    "0004-3702": ("Q1", 2.65),
    "0893-6080": ("Q1", 2.10),
    "0031-3203": ("Q1", 2.05),
    "0018-9294": ("Q1", 1.85),
    "1087-0156": ("Q1", 15.2),
    "1078-8956": ("Q1", 14.1),
    "2522-5839": ("Q1", 6.75),
    "2589-7500": ("Q1", 8.90),
    "0140-6736": ("Q1", 16.5),
    "0028-4793": ("Q1", 18.2),
    "1932-6203": ("Q1", 0.85),
    "2045-2322": ("Q1", 1.15),
    "2169-3536": ("Q2", 0.92),
    "1424-8220": ("Q2", 0.88),
    "2076-3417": ("Q2", 0.65),
    "0010-4825": ("Q1", 1.65),
    "1746-8094": ("Q1", 1.45),
    "0957-4174": ("Q1", 2.15),
    "0950-7051": ("Q1", 2.05),
}


@dataclass
class SJRRanking:
    quartile: str | None
    sjr_score: float | None


def normalize_issn(issn: str | None) -> str | None:
    if not issn:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", issn).upper()
    if len(cleaned) == 8:
        return f"{cleaned[:4]}-{cleaned[4:]}"
    return cleaned if cleaned else None


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", title)
    return " ".join(cleaned.upper().split())


def parse_sjr_float(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = raw.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_scimago_csv_text(raw_text: str) -> list[dict]:
    """Parse SCImago Journal Rank CSV content (supporting ';' and ',' delimiters) into normalized dicts."""
    if not raw_text.strip():
        return []
    text_clean = raw_text.lstrip("\ufeff")
    rows: list[dict] = []
    stream = io.StringIO(text_clean)
    reader = csv.DictReader(stream, delimiter=";")
    if not reader.fieldnames or "Issn" not in reader.fieldnames:
        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=",")

    for raw in reader:
        quartile = (raw.get("SJR Best Quartile") or "").strip().upper()
        if quartile not in {"Q1", "Q2", "Q3", "Q4"}:
            continue
        title = (raw.get("Title") or "").strip()
        norm_t = normalize_title(title)
        sjr_val = parse_sjr_float(raw.get("SJR"))
        h_idx_raw = (raw.get("H index") or "").strip()
        h_index = int(h_idx_raw) if h_idx_raw.isdigit() else None
        issn_raw = raw.get("Issn") or ""
        issns = [normalize_issn(part) for part in issn_raw.split(",")]
        for norm_issn in issns:
            if not norm_issn:
                continue
            rows.append(
                {
                    "source_id": (raw.get("Sourceid") or "").strip() or None,
                    "issn": norm_issn,
                    "title": title,
                    "normalized_title": norm_t,
                    "quartile": quartile,
                    "sjr_score": sjr_val,
                    "h_index": h_index,
                    "areas": (raw.get("Areas") or "").strip() or None,
                }
            )
    return rows


def parse_scimago_csv_rows(csv_path: Path) -> list[dict]:
    """Parse SCImago Journal Rank CSV file on disk into normalized dicts."""
    if not csv_path.exists():
        return []
    return parse_scimago_csv_text(csv_path.read_text(encoding="utf-8-sig"))


class SJRService:
    """Service to look up journal quartile based on ISSN and normalized journal title."""

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_loaded = False
        self._csv_issns: dict[str, tuple[str, float | None]] = {}
        self._csv_titles: dict[str, tuple[str, float | None]] = {}
        self._csv_path = csv_path or (
            Path(__file__).resolve().parents[2] / "data" / "scimagojr.csv"
        )

    def _ensure_csv_loaded(self) -> None:
        if self._csv_loaded:
            return
        self._csv_loaded = True
        if not self._csv_path.exists():
            return
        for row in parse_scimago_csv_rows(self._csv_path):
            self._csv_issns.setdefault(row["issn"], (row["quartile"], row["sjr_score"]))
            if row["normalized_title"]:
                self._csv_titles.setdefault(
                    row["normalized_title"], (row["quartile"], row["sjr_score"])
                )

    def lookup(self, issn: str | None, journal_title: str | None) -> SJRRanking:
        self._ensure_csv_loaded()
        norm_issn = normalize_issn(issn)
        if norm_issn:
            if norm_issn in self._csv_issns:
                q, score = self._csv_issns[norm_issn]
                return SJRRanking(quartile=q, sjr_score=score)
            if norm_issn in _KNOWN_ISSNS:
                q, score = _KNOWN_ISSNS[norm_issn]
                return SJRRanking(quartile=q, sjr_score=score)

        norm_title = normalize_title(journal_title)
        if norm_title:
            if norm_title in self._csv_titles:
                q, score = self._csv_titles[norm_title]
                return SJRRanking(quartile=q, sjr_score=score)
            if norm_title in _KNOWN_JOURNALS:
                q, score = _KNOWN_JOURNALS[norm_title]
                return SJRRanking(quartile=q, sjr_score=score)

            for known_t, (q, score) in _KNOWN_JOURNALS.items():
                if known_t in norm_title or norm_title in known_t:
                    return SJRRanking(quartile=q, sjr_score=score)

        return SJRRanking(quartile=None, sjr_score=None)

    async def lookup_db_first(
        self,
        db: AsyncSession,
        issn: str | None,
        journal_title: str | None,
    ) -> SJRRanking:
        """Query PostgreSQL sjr_journals table first, falling back to in-memory seed/CSV."""
        norm_issn = normalize_issn(issn)
        if norm_issn:
            res = await db.execute(select(SJRJournal).where(SJRJournal.issn == norm_issn).limit(1))
            row = res.scalar_one_or_none()
            if row:
                return SJRRanking(quartile=row.quartile, sjr_score=row.sjr_score)

        norm_title = normalize_title(journal_title)
        if norm_title:
            res = await db.execute(
                select(SJRJournal).where(SJRJournal.normalized_title == norm_title).limit(1)
            )
            row = res.scalar_one_or_none()
            if row:
                return SJRRanking(quartile=row.quartile, sjr_score=row.sjr_score)

        return self.lookup(issn=issn, journal_title=journal_title)


sjr_service = SJRService()
