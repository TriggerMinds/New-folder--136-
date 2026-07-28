from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source
from app.services.date_provenance import map_documentcloud_document


class DocumentCloudAPIConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        queries = cfg.get("search_queries", [])
        max_pages = cfg.get("max_pages", 2)
        per_page = cfg.get("per_page", 25)

        if not queries:
            result.error = "No search_queries configured"
            result.completed_at = datetime.now(timezone.utc)
            return result

        max_items = cfg.get("max_items", 100)
        seen_ids: set[str] = set()
        requests = 0

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for query in queries:
                if len(result.items) >= max_items:
                    break
                for page in range(1, max_pages + 1):
                    if len(result.items) >= max_items:
                        break
                    url = f"https://api.www.documentcloud.org/api/documents/search/?q={quote(query)}&page={page}&per_page={per_page}&access=public&order=created_at_desc"
                    try:
                        resp = await client.get(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
                        requests += 1
                        result.http_status = resp.status_code
                        if resp.status_code != 200:
                            if resp.status_code >= 400:
                                break
                            continue
                        data = resp.json()
                        docs = data.get("results", data.get("documents", []))
                        if not docs:
                            break
                        for doc in docs:
                            doc_id = doc.get("id")
                            if not doc_id or str(doc_id) in seen_ids:
                                continue
                            seen_ids.add(str(doc_id))
                            access = doc.get("access", "private")
                            if access != "public":
                                result.rejected_candidates += 1
                                result.rejection_reasons.append(f"non-public access: {access}")
                                continue
                            title = doc.get("title") or f"Document {doc_id}"
                            canonical_url = doc.get("canonical_url") or f"https://www.documentcloud.org/documents/{doc_id}/"
                            dp = map_documentcloud_document(doc)
                            item = DiscoveredItem(
                                source_external_id=source.external_id,
                                url=canonical_url,
                                title=title[:500] if title else f"DocumentCloud {doc_id}",
                                content=doc.get("description", "")[:5000] or None,
                                content_excerpt=doc.get("description", "")[:300] or None,
                                published_at=dp.published_at,
                                raw_metadata={
                                    "source_role": source.source_role,
                                    "source_category": source.source_category,
                                    "source": "documentcloud_api",
                                    "document_id": doc_id,
                                    "organization": doc.get("organization", ""),
                                    "access": access,
                                    "language": doc.get("language", ""),
                                    "page_count": doc.get("page_count"),
                                    "file_type": doc.get("file_type"),
                                    "noindex": doc.get("noindex", False),
                                    "slug": doc.get("slug"),
                                    "published_url": doc.get("published_url"),
                                    "related_article": doc.get("related_article"),
                                    "source_date_method": "source_api",
                                    "source_date_precision": dp.precision,
                                    "source_date_confidence": dp.confidence,
                                    "source_date_evidence": dp.evidence,
                                    "upload_date_method": "source_api",
                                    "upload_date_confidence": "authoritative",
                                    "source_created_at": str(dp.source_created_at) if dp.source_created_at else None,
                                    "source_modified_at": str(dp.source_modified_at) if dp.source_modified_at else None,
                                    "source_uploaded_at": str(dp.source_uploaded_at) if dp.source_uploaded_at else None,
                                },
                            )
                            result.items.append(item)
                            result.accepted_candidates += 1
                    except httpx.HTTPError as e:
                        result.error = f"DocumentCloud API fout: {e}"
                        result.completed_at = datetime.now(timezone.utc)
                        return result
                    except Exception as e:
                        result.error = f"DocumentCloud parse fout: {e}"
                        result.completed_at = datetime.now(timezone.utc)
                        return result

        result.requests_made = requests
        result.raw_results = len(seen_ids)
        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("documentcloud_api", DocumentCloudAPIConnector)
