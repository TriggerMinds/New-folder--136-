from datetime import datetime, timezone

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.database.models.source import Source

OBSERVED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".json", ".xml", ".zip", ".7z", ".tar", ".gz", ".sql", ".dump", ".mbox", ".eml"}


class GitHostConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        api_url = cfg.get("api_url", "")

        if not api_url:
            try:
                content, http_status = await self._fetch_url(source.poll_url)
                result.http_status = http_status
            except Exception as e:
                result.error = f"HTTP-fout: {e}"
                result.completed_at = datetime.now(timezone.utc)
                return result

            import re
            repo_links = re.findall(r'https?://[^\s<>"\']+', content)
            seen: set[str] = set()
            for link in repo_links:
                if link in seen:
                    continue
                seen.add(link)
                item = DiscoveredItem(
                    source_external_id=source.external_id,
                    url=link,
                    title=link.rsplit("/", 1)[-1] if "/" in link else link,
                    raw_metadata={"source_role": source.source_role, "source_category": source.source_category},
                )
                result.items.append(item)
            result.success = True
            result.completed_at = datetime.now(timezone.utc)
            return result

        try:
            content, http_status = await self._fetch_url(api_url)
            result.http_status = http_status
        except Exception as e:
            result.error = f"API-fout: {e}"
            result.completed_at = datetime.now(timezone.utc)
            return result

        try:
            import json
            data = json.loads(content)
            items_data = data if isinstance(data, list) else data.get("items", data.get("results", [data]))
            for entry in items_data[:100]:
                repo_url = entry.get("html_url") or entry.get("url") or entry.get("clone_url") or ""
                if not repo_url.startswith(("http://", "https://")):
                    continue
                desc = entry.get("description") or entry.get("name") or ""
                item = DiscoveredItem(
                    source_external_id=source.external_id,
                    url=repo_url,
                    title=desc[:200] if desc else repo_url.rsplit("/", 1)[-1],
                    raw_metadata={"source_role": source.source_role, "source_category": source.source_category},
                )
                result.items.append(item)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            result.error = f"JSON parsefout: {e}"

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("git_host", GitHostConnector)
