"""Voer alle ingeschakelde bronnen uit."""
import argparse
import asyncio
import platform
import sys

if platform.system() == "Windows":
    import asyncio as _asyncio
    _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

from app.database.session import async_session_factory
from app.services.source_runner import run_enabled_sources


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", default=None, help="Filter op landcode")
    parser.add_argument("--type", dest="source_type", default=None, help="Filter op brontype (rss/html)")
    args = parser.parse_args()

    async with async_session_factory() as session:
        try:
            batch = await run_enabled_sources(session, country_code=args.country, source_type=args.source_type)
            await session.commit()
            print(f"Totaal bronnen: {batch.total_sources}")
            print(f"Geslaagd: {batch.successful}")
            print(f"Mislukt: {batch.failed}")
            for r in batch.results:
                status = "OK" if r.success else "FOUT"
                print(f"  [{status}] {r.source_external_id}: {r.items_seen} items, {r.items_matched} matches, {r.claims_created} claims")
                if r.error:
                    print(f"         Fout: {r.error}")
        except Exception as e:
            await session.rollback()
            print(f"Fout: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
