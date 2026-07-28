from datetime import datetime, timezone
from urllib.parse import quote

from app.connectors.base import BaseConnector
from app.connectors.models import ConnectorResult, DiscoveredItem
from app.connectors.registry import register_connector
from app.config import settings
from app.database.models.source import Source

import httpx


class GitHubAPIConnector(BaseConnector):
    async def fetch(self, source: Source) -> ConnectorResult:
        started_at = datetime.now(timezone.utc)
        result = ConnectorResult(started_at=started_at)
        cfg = source.connector_config or {}
        queries = cfg.get("search_queries", [])
        token = cfg.get("github_token", "") or settings.github_token

        if not queries:
            result.error = "No search_queries configured"
            result.completed_at = datetime.now(timezone.utc)
            return result

        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": settings.http_user_agent}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        seen_repos: set[str] = set()

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for query in queries:
                if len(result.items) >= cfg.get("max_items", 100):
                    break
                url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=updated&per_page=50"
                try:
                    resp = await client.get(url, headers=headers)
                    result.http_status = resp.status_code
                    if resp.status_code == 403:
                        rate_remaining = resp.headers.get("X-RateLimit-Remaining", "0")
                        result.error = f"GitHub rate limit: {rate_remaining} remaining"
                        result.completed_at = datetime.now(timezone.utc)
                        return result
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    for repo in data.get("items", []):
                        repo_url = repo.get("html_url", "")
                        if not repo_url or repo_url in seen_repos:
                            continue
                        seen_repos.add(repo_url)
                        full_name = repo.get("full_name", "")
                        description = repo.get("description") or ""
                        lang = repo.get("language") or ""
                        topics = repo.get("topics") or []
                        created = repo.get("created_at")
                        updated = repo.get("updated_at")
                        pushed = repo.get("pushed_at")

                        created_dt = None
                        if created:
                            try:
                                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            except (ValueError, TypeError):
                                pass
                        pushed_dt = None
                        if pushed:
                            try:
                                pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                            except (ValueError, TypeError):
                                pass

                        item = DiscoveredItem(
                            source_external_id=source.external_id,
                            url=repo_url,
                            title=full_name or repo_url,
                            content=description,
                            content_excerpt=description[:500] if description else None,
                            published_at=created_dt,
                            raw_metadata={
                                "source_role": source.source_role,
                                "source_category": source.source_category,
                                "source": "github_api",
                                "language": lang,
                                "topics": topics,
                                "description": description,
                                "source_date_method": "source_api",
                                "source_date_precision": "exact_datetime",
                                "source_date_confidence": "high",
                                "source_created_at": created,
                                "source_modified_at": updated,
                                "source_pushed_at": pushed,
                                "upload_date_method": "repository_metadata",
                                "upload_date_confidence": "authoritative",
                                "upload_date_raw": created or "",
                            },
                        )
                        result.items.append(item)
                except httpx.HTTPError as e:
                    result.error = f"GitHub API fout: {e}"
                    result.completed_at = datetime.now(timezone.utc)
                    return result

        result.success = True
        result.completed_at = datetime.now(timezone.utc)
        return result


register_connector("github_api", GitHubAPIConnector)
