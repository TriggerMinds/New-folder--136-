from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.connectors.rss import RSSConnector
from app.database.models.source import Source


@pytest.fixture
def rss_source():
    return Source(
        external_id="test_rss",
        name="Test RSS",
        country_code="NL",
        languages=["nl"],
        source_type="rss",
        base_url="https://example.com",
        poll_url="https://example.com/feed.xml",
        connector_config={"base_url": "https://example.com", "poll_url": "https://example.com/feed.xml", "languages": ["nl"]},
    )


@pytest.mark.asyncio
async def test_rss_connector_class_available():
    from app.connectors.registry import get_connector
    connector = get_connector("rss")
    assert isinstance(connector, RSSConnector)


@pytest.mark.asyncio
async def test_rss_connector_http_error(rss_source):
    connector = RSSConnector()
    with patch.object(connector, "_fetch_url", side_effect=Exception("Connection error")):
        result = await connector.fetch(rss_source)
        assert result.success is False
        assert result.error is not None
