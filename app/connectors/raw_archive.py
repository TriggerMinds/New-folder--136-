from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import re

from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source

ARCHIVE_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".json", ".xml", ".zip", ".7z", ".tar", ".gz", ".tgz", ".rar", ".eml", ".mbox", ".sql", ".dump", ".pst", ".ost", ".txt"}


class RawArchiveConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        mode = cfg.get("archive_mode", "auto")
        item_selector = cfg.get("item_selector", "")
        link_selector = cfg.get("link_selector", "a")
        max_items = cfg.get("max_items", settings.max_items_per_source)

        try:
            content, http_status = await self._fetch_url(source.poll_url)
            result.http_status = http_status
        except Exception as e:
            result.error = f"HTTP-fout: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        if mode == "directory" or "Index of" in content or "Parent Directory" in content:
            items = self._parse_directory(content, source.poll_url, max_items)
        elif mode == "cryptome" or "href=" in content:
            items = self._parse_cryptome(content, source.poll_url, max_items)
        else:
            try:
                soup = BeautifulSoup(content, "lxml")
                if item_selector:
                    rows = soup.select(item_selector)[:max_items]
                    items = self._parse_selectors(rows, source.poll_url, max_items, link_selector, cfg)
                else:
                    items = self._parse_all_links(soup, source.poll_url, max_items)
            except Exception as e:
                result.error = f"Parsefout: {e}"
                result.completed_at = datetime.now(timezone.utc)
                return result

        for item in items:
            result.items.append(item)

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result

    def _parse_directory(self, content: str, base_url: str, max_items: int) -> list:
        items = []
        soup = BeautifulSoup(content, "lxml")
        seen = set()
        for link in soup.select("a"):
            href = link.get("href", "")
            if not href or href.startswith("?") or href == "../" or href == "/":
                continue
            full = urljoin(base_url, href)
            if full in seen:
                continue
            seen.add(full)
            text = link.get_text(strip=True)
            ext = self._ext(full)
            if ext in ARCHIVE_EXTS or ext == "":
                item = DiscoveredItem(
                    source_external_id="",
                    url=full,
                    title=text or href.rstrip("/").split("/")[-1],
                    raw_metadata={"archive_mode": "directory", "file_extension": ext},
                )
                items.append(item)
            if len(items) >= max_items:
                break
        return items

    def _parse_selectors(self, rows, base_url: str, max_items: int, link_sel: str, cfg: dict) -> list:
        items = []
        title_sel = cfg.get("title_selector", "")
        seen = set()
        for row in rows[:max_items]:
            link_el = row.select_one(link_sel) if link_sel else row
            href = link_el.get("href", "") if hasattr(link_el, "get") else ""
            if not href:
                continue
            full = urljoin(base_url, href)
            if full in seen:
                continue
            seen.add(full)
            title = ""
            if title_sel:
                t = row.select_one(title_sel)
                if t:
                    title = t.get_text(strip=True)
            if not title:
                title = link_el.get_text(strip=True) if hasattr(link_el, "get_text") else ""
            item = DiscoveredItem(
                source_external_id="",
                url=full,
                title=title or full.rsplit("/", 1)[-1],
                raw_metadata={"archive_mode": "selector"},
            )
            items.append(item)
        return items

    def _is_index_or_root(self, url: str, base_url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        lower_path = path.lower()
        if lower_path in ("", "/", "/index.html", "/index.htm", "/index.php", "/default.htm", "/default.html"):
            return True
        if lower_path.endswith(("/index.html", "/index.htm", "/index.php")):
            return True
        if url.rstrip("/") == base_url.rstrip("/"):
            return True
        return False

    def _parse_all_links(self, soup, base_url: str, max_items: int) -> list:
        items = []
        seen = set()
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            full = urljoin(base_url, href)
            if full in seen:
                continue
            seen.add(full)
            ext = self._ext(full)
            if ext not in ARCHIVE_EXTS and ext:
                continue
            if self._is_index_or_root(full, base_url):
                continue
            item = DiscoveredItem(
                source_external_id="",
                url=full,
                title=a.get_text(strip=True) or full.rsplit("/", 1)[-1],
                raw_metadata={"file_extension": ext},
            )
            items.append(item)
            if len(items) >= max_items:
                break
        return items

    def _parse_cryptome(self, content: str, base_url: str, max_items: int) -> list:
        items = []
        soup = BeautifulSoup(content, "lxml")
        seen = set()
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if not href:
                continue
            ext = self._ext(href)
            if ext not in ARCHIVE_EXTS:
                continue
            full = urljoin(base_url, href)
            if full in seen:
                continue
            seen.add(full)
            if self._is_index_or_root(full, base_url):
                continue
            text = a.get_text(strip=True) or ""
            parent = a.parent
            desc = ""
            if parent:
                desc = parent.get_text(" ", strip=True)[:500]
            parsed = urlparse(full)
            filename = parsed.path.rstrip("/").split("/")[-1] if parsed.path else ""
            item = DiscoveredItem(
                source_external_id="", url=full,
                title=text or filename, content=desc,
                content_excerpt=desc[:300],
                raw_metadata={"archive_mode": "cryptome", "filename": filename, "file_extension": ext, "page_url": base_url},
            )
            items.append(item)
            if len(items) >= max_items:
                break
        return items

    def _ext(self, url: str) -> str:
        path = urlparse(url).path.rstrip("/")
        if "." in path:
            return "." + path.rsplit(".", 1)[1].lower()
        return ""


register_connector("raw_archive", RawArchiveConnector)
