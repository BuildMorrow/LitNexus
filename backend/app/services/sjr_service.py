"""SCImago Journal Rank (SJR) lookup service.

Provides lookup of journal prestige and Scopus Quartile (Q1, Q2, Q3, Q4)
using standard ISSN and normalized journal title matching.
"""

from dataclasses import dataclass
import re

# Standard reference seed of prominent academic journals across CS, AI, Medical, and Engineering
# Can be extended with external CSV or OpenAlex source-level metadata
_KNOWN_JOURNALS: dict[str, tuple[str, float]] = {
    # CS / AI / Data Science
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
    # ISSN -> (Quartile, SJR Score)
    "0162-8828": ("Q1", 4.85),  # IEEE TPAMI
    "1532-4435": ("Q1", 3.20),  # JMLR
    "2162-237X": ("Q1", 2.95),  # IEEE TNNLS
    "0004-3702": ("Q1", 2.65),  # AI Journal
    "0893-6080": ("Q1", 2.10),  # Neural Networks
    "0031-3203": ("Q1", 2.05),  # Pattern Recognition
    "0018-9294": ("Q1", 1.85),  # IEEE TBME
    "1087-0156": ("Q1", 15.2),  # Nature Biotech
    "1078-8956": ("Q1", 14.1),  # Nature Med
    "2522-5839": ("Q1", 6.75),  # Nature Machine Intelligence
    "2589-7500": ("Q1", 8.90),  # Lancet Digital Health
    "0140-6736": ("Q1", 16.5),  # The Lancet
    "0028-4793": ("Q1", 18.2),  # NEJM
    "1932-6203": ("Q1", 0.85),  # PLOS ONE
    "2045-2322": ("Q1", 1.15),  # Scientific Reports
    "2169-3536": ("Q2", 0.92),  # IEEE Access
    "1424-8220": ("Q2", 0.88),  # Sensors
    "2076-3417": ("Q2", 0.65),  # Applied Sciences
    "0010-4825": ("Q1", 1.65),  # Computers in Biology and Medicine
    "1746-8094": ("Q1", 1.45),  # Biomedical Signal Processing and Control
    "0957-4174": ("Q1", 2.15),  # Expert Systems with Applications
    "0950-7051": ("Q1", 2.05),  # Knowledge-Based Systems
}


@dataclass
class SJRRanking:
    quartile: str | None  # "Q1", "Q2", "Q3", "Q4"
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
    # Strip punctuation and collapse whitespace
    cleaned = re.sub(r"[^\w\s]", " ", title)
    return " ".join(cleaned.upper().split())


class SJRService:
    """Service to look up journal quartile based on ISSN and normalized journal title."""

    @staticmethod
    def lookup(issn: str | None, journal_title: str | None) -> SJRRanking:
        # 1. Exact match on normalized ISSN
        norm_issn = normalize_issn(issn)
        if norm_issn and norm_issn in _KNOWN_ISSNS:
            q, score = _KNOWN_ISSNS[norm_issn]
            return SJRRanking(quartile=q, sjr_score=score)

        # 2. Exact or substring match on Journal Title
        norm_title = normalize_title(journal_title)
        if norm_title:
            if norm_title in _KNOWN_JOURNALS:
                q, score = _KNOWN_JOURNALS[norm_title]
                return SJRRanking(quartile=q, sjr_score=score)

            # Substring match for compound journal names
            for known_t, (q, score) in _KNOWN_JOURNALS.items():
                if known_t in norm_title or norm_title in known_t:
                    return SJRRanking(quartile=q, sjr_score=score)

        return SJRRanking(quartile=None, sjr_score=None)


sjr_service = SJRService()
