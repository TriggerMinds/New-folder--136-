import pytest

from app.connectors.html import HTMLConnector
from app.database.models.source import Source


@pytest.fixture
def html_source():
    return Source(
        external_id="test_html",
        name="Test HTML",
        country_code="NL",
        languages=["nl"],
        source_type="html",
        base_url="https://example.com",
        poll_url="https://example.com/list",
        connector_config={
            "item_selector": "article",
            "link_selector": "a",
            "title_selector": "h2",
            "content_selector": "p",
            "max_items": 100,
        },
    )


@pytest.mark.asyncio
async def test_html_connector_class_available():
    from app.connectors.registry import get_connector
    connector = get_connector("html")
    assert isinstance(connector, HTMLConnector)


@pytest.mark.asyncio
async def test_html_connector_requires_item_selector():
    source = Source(
        external_id="test",
        name="Test",
        country_code="NL",
        languages=["nl"],
        source_type="html",
        base_url="https://example.com",
        poll_url="https://example.com",
        connector_config={},
    )
    connector = HTMLConnector()
    result = await connector.fetch(source)
    assert result.success is False
    assert "item_selector" in (result.error or "")
