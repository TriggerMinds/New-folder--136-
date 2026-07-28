"""Voer één bron uit op external_id."""
import argparse
import asyncio
import platform
import sys

if platform.system() == "Windows":
    import asyncio as _asyncio
    _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

from app.database.session import async_session_factory
from app.database.models.source import Source
from app.services.source_runner import run_source


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--external-id", required=True, help="Bron external_id")
    args = parser.parse_args()

    async with async_session_factory() as session:
        try:
            result = await session.execute(
                select(Source).where(Source.external_id == args.external_id)
            )
            source = result.scalar_one_or_none()
            if source is None:
                print(f"Bron niet gevonden: {args.external_id}", file=sys.stderr)
                sys.exit(1)
            run_result = await run_source(source.id, session)
            await session.commit()
            print(f"Bron: {run_result.source_external_id}")
            print(f"Succes: {run_result.success}")
            print(f"Items gezien: {run_result.items_seen}")
            print(f"Matches: {run_result.items_matched}")
            print(f"Nieuwe claims: {run_result.claims_created}")
            print(f"Deduplicaties: {run_result.claims_deduplicated}")
            if run_result.error:
                print(f"Fout: {run_result.error}")
        except Exception as e:
            await session.rollback()
            print(f"Fout: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
