"""FastAPI + Jinja integration tests using real test database."""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database.session import get_db, async_session_factory


@pytest.mark.asyncio
async def test_homepage_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_artifacts_page_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/artifacts")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_distributions_page_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/distributions")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_references_page_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/references")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_sources_page_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/sources")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_source_runs_page_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/source-runs")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_api_dashboard_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    assert "unique_artifacts" in data


@pytest.mark.asyncio
async def test_api_artifacts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/artifacts")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "items" in data


@pytest.mark.asyncio
async def test_api_distribution_observations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/distribution-observations")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_api_reference_observations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/reference-observations")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_api_sources_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/sources/summary")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_entity_matching_boundaries():
    from app.services.artifact_entity_matching import match_entities

    co, eu, na = match_entities("Orders placed today", None, None, None, "NL")
    assert "DE" not in co

    co2, eu2, na2 = match_entities("file.docx", None, None, None, "NL")
    assert "EC" not in eu2

    co3, eu3, na3 = match_entities("Germany approves new law", None, None, None, "DE")
    assert "DE" in co3

    co4, eu4, na4 = match_entities("European Commission investigation", None, None, "https://example.nl/file", "NL")
    assert "European Commission" in eu4
    assert "NL" in co4


@pytest.mark.asyncio
async def test_download_blocked():
    """Test that a valid artifact returns 409 on download when disabled."""
    from app.services.artifact_discovery import register_artifact_discovery
    async with async_session_factory() as session:
        from sqlalchemy import select
        from app.database.models.source import Source
        r = await session.execute(select(Source).limit(1))
        src = r.scalar_one_or_none()
        if src:
            result = await register_artifact_discovery(
                session=session, source_id=src.id,
                url="https://example.com/test-blocked-download.pdf")
            await session.commit()
            aid = str(result.artifact.id)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r2 = await client.post(f"/api/artifacts/{aid}/download")
            assert r2.status_code == 409


@pytest.mark.asyncio
async def test_artifact_not_found_404():
    transport = ASGITransport(app=app)
    fake = "00000000-0000-0000-0000-000000000000"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(f"/api/artifacts/{fake}")
    assert r.status_code == 404
