"""Synchroniseer country packs naar de database."""
import asyncio
import platform
import sys

if platform.system() == "Windows":
    import asyncio as _asyncio
    _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

from app.database.session import async_session_factory
from app.services.source_sync import sync_country_packs_to_database


async def main() -> None:
    async with async_session_factory() as session:
        try:
            result = await sync_country_packs_to_database(session)
            await session.commit()
            print(f"Aangemaakt: {result.created}")
            print(f"Bijgewerkt: {result.updated}")
            print(f"Uitgeschakeld: {result.disabled}")
            print(f"Ongewijzigd: {result.unchanged}")
        except Exception as e:
            await session.rollback()
            print(f"Fout: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
