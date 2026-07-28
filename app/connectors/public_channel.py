from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source


class PublicChannelConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        item_selector = cfg.get("item_selector", "div.message, div.post, article, li")
        link_selector = cfg.get("link_selector", "a")
        title_selector = cfg.get("title_selector", "")
        max_items = cfg.get("max_items", settings.max_items_per_source)

        if not item_selector:
            result.error = "item_selector is verplicht"
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
                link_el = elem.select_one(link_selector) if link_selector else elem
                href = ""
                if link_el and link_el.get("href"):
                    href = urljoin(source.poll_url, link_el["href"])
                title = ""
                if title_selector:
                    title_el = elem.select_one(title_selector)
                    if title_el:
                        title = title_el.get_text(strip=True)
                body_text = elem.get_text(" ", strip=True)[:1000]

                if href and href.startswith(("http://", "https://")):
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                item = DiscoveredItem(
                    source_external_id=source.external_id,
                    url=href or source.poll_url,
                    title=title or body_text[:100] or "Untitled",
                    content=body_text,
                    content_excerpt=body_text[:500],
                    raw_metadata={"source_role": source.source_role, "source_category": source.source_category},
                )
                result.items.append(item)
            except Exception:
                continue

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("public_channel", PublicChannelConnector)
