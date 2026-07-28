import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.observed_leak_claim import ObservedLeakClaim
from app.database.models.observation import Observation
from app.database.models.audit_event import AuditEvent
from app.services.claim_registration import register_observed_leak_claim
from app.repositories.claims import ClaimRepository
from app.repositories.observations import ObservationRepository
from app.repositories.audit import AuditRepository


async def _count_claims(db: AsyncSession) -> int:
    repo = ClaimRepository(db)
    return await repo.count_claims()


async def _count_observations(db: AsyncSession) -> int:
    result = await db.execute(select(Observation))
    return len(result.scalars().all())


async def _count_audit_events(db: AsyncSession) -> int:
    repo = AuditRepository(db)
    return await repo.count_audit_events()


@pytest.mark.asyncio
async def test_register_new_claim(db_session: AsyncSession):
    result = await register_observed_leak_claim(
        session=db_session,
        title_original="Test claim",
        first_observed_url="https://example.com/test1",
        source_language="nl",
        countries=["NL"],
    )
    assert result.is_new is True
    assert result.dedup_type is None
    assert result.claim.title_original == "Test claim"
    assert result.claim.first_observed_host == "example.com"
    assert result.observation.canonical_url == "https://example.com/test1"


@pytest.mark.asyncio
async def test_register_creates_claim_and_observation_and_audit(db_session: AsyncSession):
    n_claims = await _count_claims(db_session)
    n_obs = await _count_observations(db_session)
    n_audit = await _count_audit_events(db_session)

    await register_observed_leak_claim(
        session=db_session,
        title_original="Audit test",
        first_observed_url="https://example.com/audit-test",
    )

    assert await _count_claims(db_session) == n_claims + 1
    assert await _count_observations(db_session) == n_obs + 1
    assert await _count_audit_events(db_session) == n_audit + 1


@pytest.mark.asyncio
async def test_dedup_on_canonical_url(db_session: AsyncSession):
    result1 = await register_observed_leak_claim(
        session=db_session,
        title_original="Eerste claim",
        first_observed_url="https://example.com/dup",
    )
    result2 = await register_observed_leak_claim(
        session=db_session,
        title_original="Tweede claim (zou gedupliceerd moeten zijn)",
        first_observed_url="https://example.com/dup",
    )
    assert result1.is_new is True
    assert result2.is_new is False
    assert result2.dedup_type == "canonical_url"
    assert result2.claim.id == result1.claim.id


@pytest.mark.asyncio
async def test_dedup_on_content_hash(db_session: AsyncSession):
    result1 = await register_observed_leak_claim(
        session=db_session,
        title_original="Hash claim 1",
        first_observed_url="https://example.com/hash1",
        content_excerpt="Exact dezelfde inhoud",
    )
    result2 = await register_observed_leak_claim(
        session=db_session,
        title_original="Hash claim 2",
        first_observed_url="https://example.com/hash2",
        content_excerpt="Exact dezelfde inhoud",
    )
    assert result1.is_new is True
    assert result2.is_new is False
    assert result2.dedup_type == "content_hash"
    assert result2.claim.id == result1.claim.id


@pytest.mark.asyncio
async def test_dedup_updates_last_observed_at(db_session: AsyncSession):
    from datetime import datetime, timedelta
    future = datetime.now()
    past = future - timedelta(hours=1)
    result1 = await register_observed_leak_claim(
        session=db_session,
        title_original="Tijdtest",
        first_observed_url="https://example.com/time-test",
        observed_at=past,
    )
    result2 = await register_observed_leak_claim(
        session=db_session,
        title_original="Tijdtest (dup)",
        first_observed_url="https://example.com/time-test",
        observed_at=future,
    )
    claim = await ClaimRepository(db_session).get_claim(result1.claim.id)
    assert claim is not None
    assert claim.last_observed_at > past
    assert claim.last_observed_at >= result1.claim.first_observed_at


@pytest.mark.asyncio
async def test_chronological_order(db_session: AsyncSession):
    from datetime import datetime, timedelta
    now = datetime.now()
    await register_observed_leak_claim(
        session=db_session,
        title_original="Oudste",
        first_observed_url="https://example.com/chrono1",
        observed_at=now - timedelta(days=2),
    )
    await register_observed_leak_claim(
        session=db_session,
        title_original="Middelste",
        first_observed_url="https://example.com/chrono2",
        observed_at=now - timedelta(days=1),
    )
    await register_observed_leak_claim(
        session=db_session,
        title_original="Nieuwste",
        first_observed_url="https://example.com/chrono3",
        observed_at=now,
    )
    repo = ClaimRepository(db_session)
    claims = await repo.list_claims_chronological(limit=10, offset=0)
    titles = [c.title_original for c in claims]
    assert titles == ["Nieuwste", "Middelste", "Oudste"]


@pytest.mark.asyncio
async def test_audit_event_on_registration(db_session: AsyncSession):
    result = await register_observed_leak_claim(
        session=db_session,
        title_original="Audit event test",
        first_observed_url="https://example.com/audit-event-test",
    )
    repo = AuditRepository(db_session)
    events = await repo.list_audit_events(claim_id=result.claim.id)
    assert len(events) == 1
    assert events[0].event_type == "claim_registered"
    assert events[0].claim_id == result.claim.id
