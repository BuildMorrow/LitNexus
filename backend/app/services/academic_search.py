import asyncio
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.services.sjr_service import sjr_service


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
    scopus_quartile: str | None = None
    discovery_source: str = "keyword"
    seed_distance: int = 0


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


def _extract_short_openalex_id(openalex_id: str) -> str:
    return openalex_id.rstrip("/").split("/")[-1]


def _parse_openalex_work(
    item: dict,
    *,
    discovery_source: str = "keyword",
    seed_distance: int = 0,
) -> ScholarlyWork:
    """Parse one OpenAlex work JSON object into ScholarlyWork with SJR enrichment."""
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
    journal_name = source.get("display_name")
    issn_val = issns[0] if issns else None
    sjr_res = sjr_service.lookup(issn=issn_val, journal_title=journal_name)

    return ScholarlyWork(
        openalex_id=item.get("id"),
        doi=clean_doi,
        title=item.get("display_name") or item.get("title") or "Untitled",
        authors=authors,
        journal=journal_name,
        issn=issn_val,
        year=item.get("publication_year"),
        abstract=reconstruct_abstract(item.get("abstract_inverted_index")),
        citation_count=item.get("cited_by_count") or 0,
        pdf_url=primary_loc.get("pdf_url") or (item.get("open_access") or {}).get("oa_url"),
        scopus_quartile=sjr_res.quartile,
        discovery_source=discovery_source,
        seed_distance=seed_distance,
    )


async def search_openalex(
    query: str,
    limit: int = 50,
    year_from: int | None = None,
    year_to: int | None = None,
    open_access_only: bool = False,
) -> list[ScholarlyWork]:
    """Fetch scholarly works from the free OpenAlex API."""
    settings = get_settings()
    filters = ["has_abstract:true"]
    if year_from and year_to:
        filters.append(f"publication_year:{year_from}-{year_to}")
    elif year_from:
        filters.append(f"from_publication_date:{year_from}-01-01")
    elif year_to:
        filters.append(f"to_publication_date:{year_to}-12-31")

    if open_access_only:
        filters.append("is_oa:true")

    params: dict[str, str | int] = {
        "search": query,
        "per-page": min(limit, 200),
        "filter": ",".join(filters),
    }
    if settings.OPENALEX_MAILTO:
        params["mailto"] = settings.OPENALEX_MAILTO

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get("https://api.openalex.org/works", params=params)
        resp.raise_for_status()
        data = resp.json()

    return [
        _parse_openalex_work(item, discovery_source="keyword", seed_distance=0)
        for item in data.get("results", [])
    ]


async def fetch_backward_references(
    client: httpx.AsyncClient,
    openalex_id: str,
    limit: int = 15,
    distance: int = 1,
    mailto: str = "",
) -> list[ScholarlyWork]:
    """Fetch papers referenced by a seed work (Backward Snowballing)."""
    short_id = _extract_short_openalex_id(openalex_id)
    params = {"mailto": mailto} if mailto else {}
    seed_resp = await client.get(f"https://api.openalex.org/works/{short_id}", params=params)
    seed_resp.raise_for_status()
    referenced_ids = [
        _extract_short_openalex_id(ref)
        for ref in (seed_resp.json().get("referenced_works") or [])[:limit]
        if ref
    ]
    if not referenced_ids:
        return []

    batch_params: dict[str, str | int] = {
        "filter": f"openalex_id:{'|'.join(referenced_ids)}",
        "per-page": len(referenced_ids),
    }
    if mailto:
        batch_params["mailto"] = mailto
    works_resp = await client.get("https://api.openalex.org/works", params=batch_params)
    works_resp.raise_for_status()
    return [
        _parse_openalex_work(
            item, discovery_source="backward_snowball", seed_distance=distance
        )
        for item in works_resp.json().get("results", [])
    ]


async def fetch_forward_citations(
    client: httpx.AsyncClient,
    openalex_id: str,
    limit: int = 15,
    distance: int = 1,
    mailto: str = "",
) -> list[ScholarlyWork]:
    """Fetch newer papers citing a seed work (Forward Snowballing)."""
    short_id = _extract_short_openalex_id(openalex_id)
    params: dict[str, str | int] = {
        "filter": f"cites:{short_id},has_abstract:true",
        "per-page": min(limit, 50),
        "sort": "cited_by_count:desc",
    }
    if mailto:
        params["mailto"] = mailto
    resp = await client.get("https://api.openalex.org/works", params=params)
    resp.raise_for_status()
    return [
        _parse_openalex_work(
            item, discovery_source="forward_snowball", seed_distance=distance
        )
        for item in resp.json().get("results", [])
    ]


async def run_two_way_snowball(
    seed_openalex_ids: list[str],
    limit_per_direction: int = 15,
    distance: int = 1,
) -> list[ScholarlyWork]:
    """Run concurrent backward & forward citation snowballing across seed OpenAlex IDs."""
    clean_seeds = [s for s in seed_openalex_ids if s]
    if not clean_seeds:
        return []

    settings = get_settings()
    discovered: list[ScholarlyWork] = []
    seen_keys: set[str] = {s.rstrip("/").split("/")[-1] for s in clean_seeds}

    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = []
        for seed_id in clean_seeds:
            tasks.append(
                fetch_backward_references(
                    client,
                    seed_id,
                    limit=limit_per_direction,
                    distance=distance,
                    mailto=settings.OPENALEX_MAILTO,
                )
            )
            tasks.append(
                fetch_forward_citations(
                    client,
                    seed_id,
                    limit=limit_per_direction,
                    distance=distance,
                    mailto=settings.OPENALEX_MAILTO,
                )
            )
        batches = await asyncio.gather(*tasks, return_exceptions=True)

    for batch in batches:
        if isinstance(batch, BaseException):
            continue
        for work in batch:
            oa_short = _extract_short_openalex_id(work.openalex_id) if work.openalex_id else None
            dedup_key = oa_short or (work.doi or work.title.lower())
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            discovered.append(work)

    return discovered
