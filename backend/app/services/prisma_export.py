"""Academic PRISMA 2020 SVG Flow Diagram & Multi-Sheet Excel (.xlsx) Export Service."""

import io
from html import escape

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def generate_prisma_flow_svg(
    *,
    identified: int,
    screened: int,
    excluded: int,
    included: int,
) -> str:
    """Generate a clean publication-ready PRISMA 2020 4-stage SVG flow diagram."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 390" width="100%" height="auto" font-family="system-ui, -apple-system, sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b"/>
    </marker>
  </defs>
  <rect width="680" height="390" rx="12" fill="#0f172a"/>
  <!-- Identification -->
  <rect x="60" y="24" width="280" height="66" rx="8" fill="#1e293b" stroke="#6366f1" stroke-width="2"/>
  <text x="200" y="49" fill="#c7d2fe" font-size="12" font-weight="700" text-anchor="middle">1. IDENTIFICATION</text>
  <text x="200" y="71" fill="#f8fafc" font-size="13" text-anchor="middle">Records Identified (n = {identified})</text>
  <line x1="200" y1="90" x2="200" y2="122" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- Screening -->
  <rect x="60" y="126" width="280" height="66" rx="8" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>
  <text x="200" y="151" fill="#bae6fd" font-size="12" font-weight="700" text-anchor="middle">2. SCREENING (AL + Peer Review)</text>
  <text x="200" y="173" fill="#f8fafc" font-size="13" text-anchor="middle">Records Screened (n = {screened})</text>

  <!-- Excluded branch -->
  <line x1="340" y1="159" x2="404" y2="159" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="408" y="126" width="220" height="66" rx="8" fill="#2d1620" stroke="#f43f5e" stroke-width="2"/>
  <text x="518" y="151" fill="#fda4af" font-size="12" font-weight="700" text-anchor="middle">RECORDS EXCLUDED</text>
  <text x="518" y="173" fill="#ffe4e6" font-size="13" text-anchor="middle">Excluded Studies (n = {excluded})</text>

  <line x1="200" y1="192" x2="200" y2="232" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- Eligibility & Included -->
  <rect x="60" y="236" width="280" height="66" rx="8" fill="#0f2922" stroke="#10b981" stroke-width="2.5"/>
  <text x="200" y="261" fill="#6ee7b7" font-size="12" font-weight="700" text-anchor="middle">3. INCLUDED CORE STUDIES</text>
  <text x="200" y="283" fill="#ecfdf5" font-size="13" font-weight="700" text-anchor="middle">Final Included Corpus (n = {included})</text>

  <text x="340" y="352" fill="#94a3b8" font-size="11" text-anchor="middle">PRISMA 2020 Automated Funnel — LitNexus ({escape("Active Learning + Grounded Verifier")})</text>
</svg>"""


def generate_slr_excel_bytes(
    *,
    project_title: str,
    papers: list,
    claims_rows: list[tuple],
    edges: list,
    gaps: list,
) -> bytes:
    """Export Papers, Comparative Evidence Matrix, and Conflicts/Gaps to multi-sheet XLSX."""
    wb = Workbook()
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    def _style_headers(ws, headers: list[str], widths: list[int]) -> None:
        ws.append(headers)
        for col_idx, width in enumerate(widths, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            col_letter = cell.column_letter
            ws.column_dimensions[col_letter].width = width

    # Sheet 1: Screened Corpus
    ws_papers = wb.active
    ws_papers.title = "Papers & Screening"
    _style_headers(
        ws_papers,
        [
            "Title",
            "Authors",
            "Journal",
            "Year",
            "Quartile",
            "DOI",
            "Discovery Source",
            "Screening Status",
            "Screening Source",
            "AI Rationale",
        ],
        [48, 30, 28, 10, 12, 24, 18, 16, 16, 48],
    )
    for p in papers:
        rationale = (p.screening_rationale or {}).get("reason", "")
        ws_papers.append(
            [
                p.title,
                "; ".join(p.authors or []),
                p.journal or "",
                p.year or "",
                p.scopus_quartile or "",
                p.doi or "",
                getattr(p, "discovery_source", "keyword"),
                p.screening_status.value,
                p.screening_source.value,
                rationale,
            ]
        )

    # Sheet 2: Comparative Evidence Matrix
    ws_matrix = wb.create_sheet("Evidence Matrix")
    _style_headers(
        ws_matrix,
        [
            "Paper Title",
            "Year",
            "Quartile",
            "Claim",
            "Methodology",
            "Dataset",
            "Metrics",
            "Assumptions",
            "Page / Section",
            "Evidence Quote",
        ],
        [40, 10, 10, 44, 28, 26, 26, 28, 22, 52],
    )
    for claim, paper in claims_rows:
        pin = (
            f"p.{claim.page_number} ({claim.section_title or ''})"
            if claim.page_number
            else (claim.section_title or "Abstract")
        )
        ws_matrix.append(
            [
                paper.title,
                paper.year or "",
                paper.scopus_quartile or "",
                claim.claim_text,
                claim.methodology or "",
                claim.dataset or "",
                claim.metric_summary or "",
                "; ".join(claim.assumptions or []),
                pin,
                claim.evidence_quote or "",
            ]
        )

    # Sheet 3: Conflicts & Research Gaps
    ws_gaps = wb.create_sheet("Conflicts & Gaps")
    _style_headers(
        ws_gaps,
        ["Record Type", "Category / Score", "Title / Debate Summary", "Hypothesis / Suggested Direction"],
        [18, 20, 56, 56],
    )
    ws_gaps.append(["Project", project_title, "", ""])
    for e in edges:
        ws_gaps.append(
            [
                "Conflict Edge",
                f"{e.relation_type.value} ({e.confidence:.2f})",
                e.debate_summary,
                e.root_cause_hypothesis or "",
            ]
        )
    for g in gaps:
        ws_gaps.append(
            [
                "Research Gap",
                f"Novelty: {g.novelty_score:.2f}",
                f"{g.title}: {g.description}",
                g.suggested_direction or "",
            ]
        )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
