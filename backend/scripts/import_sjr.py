"""Offline importer for SCImago Journal Rank (scimagojr.csv) into PostgreSQL sjr_journals.

Usage:
    cd backend
    python -m scripts.import_sjr --csv data/scimagojr.csv
"""

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import delete

from app.core.database import AsyncSessionLocal, init_db
from app.models.sjr import SJRJournal
from app.services.sjr_service import parse_scimago_csv_rows


async def import_sjr_csv(csv_path: Path, batch_size: int = 2000) -> int:
    rows = parse_scimago_csv_rows(csv_path)
    if not rows:
        return 0

    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(SJRJournal))
        for start in range(0, len(rows), batch_size):
            batch = [SJRJournal(**item) for item in rows[start : start + batch_size]]
            db.add_all(batch)
            await db.flush()
        await db.commit()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import SCImago SJR CSV into PostgreSQL.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/scimagojr.csv"),
        help="Path to scimagojr.csv",
    )
    args = parser.parse_args()
    if not args.csv.exists():
        print(f"File not found: {args.csv}")
        raise SystemExit(1)

    inserted = asyncio.run(import_sjr_csv(args.csv))
    print(f"Imported {inserted} SJR ISSN journal records into PostgreSQL.")


if __name__ == "__main__":
    main()
