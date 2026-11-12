from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class ScholarlyWork:
    openalex_id: str | None
    doi: str | None
    title: str
    authors: list[str]
    journal: str | None
    issn: str | None
    year: int | None
    abstract: str | None
    citation_count: int
    pdf_url: str | None


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """OpenAlex returns abstracts as word -> position lists; reconstruct plain text."""
    if not inverted_index:
        return None
    words: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    if not words:
        return None
    return " ".join(words[i] for i in sorted(words.keys()))


async def search_openalex(query: str, limit: int = 50) -> list[ScholarlyWork]:
    """Fetch scholarly works from the free OpenAlex API."""
    settings = get_settings()
    params: dict[str, str | int] = {
        "search": query,
        "per-page": min(limit, 200),
        "filter": "has_abstract:true",
    }
    if settings.OPENALEX_MAILTO:
        params["mailto"] = settings.OPENALEX_MAILTO

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get("https://api.openalex.org/works", params=params)
        resp.raise_for_status()
        data = resp.json()

    works: list[ScholarlyWork] = []
    for item in data.get("results", []):
        primary_loc = item.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        issns = source.get("issn") or []
        authorships = item.get("authorships") or []
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in authorships
            if a.get("author", {}).get("display_name")
        ]
        raw_doi = item.get("doi") or ""
        clean_doi = raw_doi.replace("https://doi.org/", "") if raw_doi else None

        works.append(
            ScholarlyWork(
                openalex_id=item.get("id"),
                doi=clean_doi,
                title=item.get("display_name") or item.get("title") or "Untitled",
                authors=authors,
                journal=source.get("display_name"),
                issn=issns[0] if issns else None,
                year=item.get("publication_year"),
                abstract=reconstruct_abstract(item.get("abstract_inverted_index")),
                citation_count=item.get("cited_by_count") or 0,
                pdf_url=primary_loc.get("pdf_url")
                or (item.get("open_access") or {}).get("oa_url"),
            )
        )
    return works
