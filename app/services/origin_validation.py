from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class OriginValidationResult:
    url: str
    final_url: str = ""
    status_code: int = 0
    content_type: str = ""
    content_length: int = 0
    reachable: bool = False
    blocked: bool = False
    oversized: bool = False
    invalid_content: bool = False
    validation_error: str = ""


async def validate_origin_candidate(url: str) -> OriginValidationResult:
    result = OriginValidationResult(url=url)
    headers = {"User-Agent": settings.http_user_agent}

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True, max_redirects=5) as client:
            response = await client.head(url, headers=headers)
            result.final_url = str(response.url)
            result.status_code = response.status_code

            if response.status_code >= 400:
                result.validation_error = f"HTTP {response.status_code}"
                return result

            ct = response.headers.get("content-type", "")
            result.content_type = ct
            cl = response.headers.get("content-length", "0")
            result.content_length = int(cl) if cl.isdigit() else 0

            if result.content_length > settings.http_max_response_bytes:
                result.oversized = True
                result.validation_error = f"Oversized: {result.content_length} bytes"
                return result

            if ct and not _is_reasonable_content_type(ct):
                result.invalid_content = True
                result.validation_error = f"Onverwacht content-type: {ct}"
                return result

            result.reachable = True

    except httpx.ConnectError:
        result.blocked = True
        result.validation_error = "ConnectError: host unreachable"
    except httpx.TimeoutException:
        result.validation_error = "Timeout"
    except httpx.HTTPStatusError as e:
        result.status_code = e.response.status_code
        result.validation_error = f"HTTP {e.response.status_code}"
    except Exception as e:
        result.validation_error = str(e)

    return result


def _is_reasonable_content_type(ct: str) -> bool:
    ct_lower = ct.lower()
    allowed_prefixes = [
        "text/html", "text/plain", "text/xml", "application/xml",
        "application/json", "application/pdf", "application/zip",
        "application/x-tar", "application/gzip", "application/octet-stream",
        "application/x-7z-compressed", "application/vnd.openxmlformats-officedocument",
        "application/msword", "application/vnd.ms-excel",
        "message/rfc822",
    ]
    for prefix in allowed_prefixes:
        if ct_lower.startswith(prefix):
            return True
    return False
