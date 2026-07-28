from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser

from app.connectors.base import BaseConnector
from app.connectors.exceptions import ConnectorHTTPError, ConnectorParseError
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.database.models.source import Source


class RSSConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)

        try:
            content, http_status = await self._fetch_url(source.poll_url)
            result.http_status = http_status
        except Exception as e:
            result.error = f"HTTP-fout bij ophalen feed: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        try:
            feed = feedparser.parse(content)
        except Exception as e:
            result.error = f"Feed parsefout: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        if feed.bozo and not feed.entries:
            result.error = f"Feed bozo-fout: {feed.bozo_exception}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        for entry in feed.entries:
            try:
                link = entry.get("link", "")
                if not link.startswith(("http://", "https://")):
                    continue

                title = entry.get("title")
                summary = entry.get("summary") or entry.get("description")
                content_text = None
                if hasattr(entry, "content") and entry.content:
                    content_text = entry.content[0].get("value", "")

                published = None
                if entry.get("published_parsed"):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif entry.get("updated_parsed"):
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                raw_meta = {}
                if entry.get("id"):
                    raw_meta["feed_id"] = entry.id
                if entry.get("author"):
                    raw_meta["author"] = entry.author
                if entry.get("tags"):
                    raw_meta["tags"] = [t.get("term", "") for t in entry.tags if hasattr(t, "get")]
                if entry.get("published"):
                    raw_meta["published_string"] = entry.published

                item = DiscoveredItem(
                    source_external_id=source.external_id,
                    url=link,
                    title=title,
                    content=content_text or summary or "",
                    content_excerpt=(summary or "")[:500] if summary else None,
                    published_at=published,
                    raw_metadata=raw_meta,
                )
                result.items.append(item)
            except Exception:
                continue

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("rss", RSSConnector)
