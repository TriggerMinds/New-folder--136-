import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source import Source
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.services.artifact_discovery import register_artifact_discovery
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository, DistributionObservationRepository


@pytest.fixture
def test_source_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def source_in_db(db_session: AsyncSession, test_source_id: uuid.UUID) -> Source:
    src = Source(
        id=test_source_id, external_id="test_artifact_source", name="Test Source",
        country_code="NL", languages=["nl"], source_type="raw_archive",
        source_layer="primary_raw", can_create_artifact_discovery=True,
        base_url="https://example.com", poll_url="https://example.com", enabled=True,
    )
    db_session.add(src)
    await db_session.flush()
    return src


@pytest.mark.asyncio
async def test_register_artifact_discovery_creates_record(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    res = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/test.pdf", title="Test Document")
    assert res.is_new
    assert res.artifact.artifact_type == "document"
    assert res.artifact.file_extension == ".pdf"
    assert res.artifact.filename == "test.pdf"
    assert res.artifact.acquisition_status == "metadata_only"


@pytest.mark.asyncio
async def test_register_artifact_creates_distribution(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    res = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/data.zip", title="Data Archive")
    repo = DistributionObservationRepository(db_session)
    dists = await repo.list_for_artifact(res.artifact.id)
    assert len(dists) == 1
    assert dists[0].distribution_type == "origin_candidate"


@pytest.mark.asyncio
async def test_artifact_type_classification(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    cases = [
        ("https://example.com/doc.pdf", "document", ".pdf"),
        ("https://example.com/data.csv", "dataset", ".csv"),
        ("https://example.com/backup.zip", "archive_file", ".zip"),
        ("https://example.com/email.eml", "email_archive", ".eml"),
        ("https://example.com/dump.sql", "database_dump", ".sql"),
    ]
    for url, expected_type, expected_ext in cases:
        res = await register_artifact_discovery(session=db_session, source_id=test_source_id, url=url, title="Test")
        assert res.artifact.artifact_type == expected_type, f"Expected {expected_type} for {url}"
        assert res.artifact.file_extension == expected_ext, f"Expected {expected_ext} for {url}"


@pytest.mark.asyncio
async def test_metadata_first_default(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    res = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/document.pdf")
    assert res.artifact.acquisition_status == "metadata_only"


@pytest.mark.asyncio
async def test_artifact_can_be_listed(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/one.pdf")
    await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/two.pdf")
    repo = ArtifactDiscoveryRepository(db_session)
    all_items = await repo.list_discoveries(limit=10, offset=0)
    assert len(all_items) >= 2


@pytest.mark.asyncio
async def test_dedup_canonical_locator(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    r1 = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/dup.pdf")
    r2 = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/dup.pdf")
    assert r1.is_new
    assert not r2.is_new
    assert r2.deduplication_type == "canonical_locator"
    assert r1.artifact.id == r2.artifact.id


@pytest.mark.asyncio
async def test_dedup_does_not_double_count(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    repo = ArtifactDiscoveryRepository(db_session)
    before = await repo.count_discoveries()
    await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/count-test.pdf")
    await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/count-test.pdf")
    after = await repo.count_discoveries()
    assert after == before + 1


@pytest.mark.asyncio
async def test_distribution_not_duplicated_for_same_locator(db_session: AsyncSession, source_in_db: Source, test_source_id: uuid.UUID):
    r1 = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/dist.pdf")
    assert r1.distribution_created
    r2 = await register_artifact_discovery(session=db_session, source_id=test_source_id, url="https://example.com/dist.pdf")
    assert not r2.distribution_created
