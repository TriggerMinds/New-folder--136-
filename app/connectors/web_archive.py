from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source


class WebArchiveConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        item_selector = cfg.get("item_selector", "a")
        max_items = cfg.get("max_items", settings.max_items_per_source)

        if not item_selector:
            result.error = "item_selector is verplicht in connector_config"
            result.completed_at = datetime.now(timezone.utc)
            return result

        try:
            content, http_status = await self._fetch_url(source.poll_url)
            result.http_status = http_status
        except Exception as e:
            result.error = f"HTTP-fout: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception as e:
            result.error = f"Parsefout: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        seen_urls: set[str] = set()
        for elem in soup.select(item_selector)[:max_items]:
            try:
                href = elem.get("href") or ""
                if href:
                    href = urljoin(source.poll_url, href)
                if not href.startswith(("http://", "https://")):
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                title = elem.get_text(strip=True) or href.rsplit("/", 1)[-1]
                item = DiscoveredItem(
                    source_external_id=source.external_id,
                    url=href,
                    title=title,
                    raw_metadata={"source_role": source.source_role, "source_category": source.source_category},
                )
                result.items.append(item)
            except Exception:
                continue

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("web_archive", WebArchiveConnector)
