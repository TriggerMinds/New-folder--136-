import asyncio
import os
import sys
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database.base import Base
from app.database.models import (
    ObservedLeakClaim,
    Observation,
    Source,
    AuditEvent,
    SourceRun,
    SourceSignal,
    ArtifactDiscovery,
    DistributionObservation,
    ReferenceObservation,
    ArtifactAcquisition,
)

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://eu_leak:change_me@localhost:5432/eu_leak_test",
)


@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return engine


ENUM_TYPES_SQL = """
DO $$ BEGIN
    CREATE TYPE authenticity_status AS ENUM (
        'unexamined', 'verified_authentic', 'likely_authentic',
        'likely_fabricated', 'confirmed_fabricated', 'disputed', 'unverifiable'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE provenance_status AS ENUM (
        'unknown', 'traced', 'partially_traced', 'attributed',
        'confirmed_anonymous', 'confirmed_whistleblower', 'confirmed_state_actor'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE content_access_status AS ENUM (
        'public', 'paywalled', 'restricted', 'deleted', 'unavailable'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
    CREATE TYPE ai_enrichment_status AS ENUM (
        'pending', 'enriched', 'failed', 'skipped'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
"""


@pytest.fixture
def test_source_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.execute(text(ENUM_TYPES_SQL))
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
