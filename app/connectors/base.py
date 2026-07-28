from abc import ABC, abstractmethod

import httpx

from app.config import settings
from app.database.models.source import Source
from app.connectors.models import ConnectorResult


class BaseConnector(ABC):
    def __init__(self):
        self.timeout = settings.http_timeout_seconds
        self.max_bytes = settings.http_max_response_bytes
        self.user_agent = settings.http_user_agent

    async def _fetch_url(self, url: str) -> tuple[str, int | None]:
        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            content = response.text[:self.max_bytes]
            return content, response.status_code

    @abstractmethod
    async def fetch(self, source: Source) -> ConnectorResult:
        ...
