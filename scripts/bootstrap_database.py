"""Bootstrap script: maakt de database aan via de default PostgreSQL-verbinding
als deze nog niet bestaat. Gebruikt de DATABASE_URL uit .env om de naam te
extraheren en maakt de database aan op localhost:5432.
"""
import asyncio
import re
import sys
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def bootstrap() -> None:
    match = re.match(
        r"postgresql\+psycopg://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)",
        settings.database_url,
    )
    if not match:
        print("Fout: kan DATABASE_URL niet parsen", file=sys.stderr)
        sys.exit(1)

    user, password, host, port_str, dbname = match.groups()
    port = port_str or "5432"
    admin_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/postgres"

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": dbname},
            )
            if result.scalar():
                print(f"Database '{dbname}' bestaat al.")
            else:
                await conn.execute(text(f'CREATE DATABASE "{dbname}"'))
                print(f"Database '{dbname}' aangemaakt.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(bootstrap())
