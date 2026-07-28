from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source
from app.services.date_provenance import map_internet_archive

ACCEPT_MEDIATYPES = {"dataset", "collection", "texts", "data", "software", "archives"}
REJECT_MEDIATYPES = {"audio", "etree", "movies", "image", "web", "account", "broadcast"}


class InternetArchiveAPIConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        queries = cfg.get("search_queries", [])

        if not queries:
            result.error = "No search_queries configured"
            result.completed_at = datetime.now(timezone.utc)
            return result

        max_items = cfg.get("max_items", 200)
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for query in queries:
                if len(result.items) >= max_items:
                    break
                search_url = f"https://archive.org/advancedsearch.php?q={quote(query)}&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=description&fl%5B%5D=creator&fl%5B%5D=date&fl%5B%5D=publicdate&fl%5B%5D=addeddate&fl%5B%5D=mediatype&fl%5B%5D=collection&fl%5B%5D=language&fl%5B%5D=subject&fl%5B%5D=downloads&sort%5B%5D=publicdate+desc&rows=100&output=json"
                try:
                    resp = await client.get(search_url, headers={"User-Agent": self.user_agent})
                    result.http_status = resp.status_code
                    if resp.status_code != 200:
                        result.error = f"Archive.org API HTTP {resp.status_code}"
                        result.completed_at = datetime.now(timezone.utc)
                        return result
                    data = resp.json()
                    items_data = data.get("response", {}).get("docs", [])
                    for entry in items_data:
                        identifier = entry.get("identifier", "")
                        if not identifier or identifier in seen_ids:
                            continue
                        seen_ids.add(identifier)
                        mediatype = (entry.get("mediatype") or "").lower()

                        if mediatype in REJECT_MEDIATYPES:
                            continue
                        if mediatype not in ACCEPT_MEDIATYPES:
                            continue

                        title = entry.get("title") or identifier
                        desc_raw = entry.get("description", "") or ""
                        if isinstance(desc_raw, list):
                            desc_raw = " | ".join(str(d) for d in desc_raw)

                        dp = map_internet_archive(entry)

                        item = DiscoveredItem(
                            source_external_id=source.external_id,
                            url=f"https://archive.org/details/{identifier}",
                            title=title[:500] if title else identifier,
                            content=desc_raw[:5000] or None,
                            content_excerpt=desc_raw[:300] or None,
                            published_at=dp.published_at,
                            raw_metadata={
                                "source_role": source.source_role,
                                "source_category": source.source_category,
                                "source": "internet_archive_api",
                                "mediatype": mediatype,
                                "collection": entry.get("collection", ""),
                                "creator": entry.get("creator", ""),
                                "subject": entry.get("subject", []),
                                "language": entry.get("language", ""),
                                "identifier": identifier,
                                "publicdate": entry.get("publicdate"),
                                "addeddate": entry.get("addeddate"),
                                "source_date_method": "source_api",
                                "source_date_precision": dp.precision,
                                "source_date_confidence": dp.confidence,
                                "source_date_evidence": dp.evidence,
                                "upload_date_method": "archive_metadata",
                                "upload_date_confidence": "authoritative",
                                "upload_date_raw": entry.get("addeddate") or entry.get("publicdate") or "",
                                "source_uploaded_at": str(dp.source_uploaded_at) if dp.source_uploaded_at else None,
                                "source_added_at": str(dp.source_added_at) if dp.source_added_at else None,
                            },
                        )
                        result.items.append(item)
                except httpx.HTTPError as e:
                    result.error = f"Archive.org API fout: {e}"
                    result.completed_at = datetime.now(timezone.utc)
                    return result
                except Exception as e:
                    result.error = f"Archive.org parse fout: {e}"
                    result.completed_at = datetime.now(timezone.utc)
                    return result

        result.requests_made = len(queries)
        result.raw_results = len(seen_ids)
        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("internet_archive_api", InternetArchiveAPIConnector)
