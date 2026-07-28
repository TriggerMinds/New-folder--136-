from datetime import datetime, timezone, timedelta

from app.config import settings


def classify_freshness(
    published_at: datetime | None,
    source_uploaded_at: datetime | None,
    source_modified_at: datetime | None,
    first_observed_at: datetime | None,
) -> str:
    now = datetime.now(timezone.utc)
    window = timedelta(days=settings.freshness_window_days)

    has_reliable_pub = published_at is not None
    has_reliable_upload = source_uploaded_at is not None
    is_recently_observed = first_observed_at is not None and (now - first_observed_at) <= window

    if has_reliable_pub and (now - published_at) <= window:
        return "newly_published"
    if has_reliable_upload and (now - source_uploaded_at) <= window:
        return "newly_uploaded"
    if source_modified_at and (now - source_modified_at) <= window:
        return "recently_updated"
    if is_recently_observed and (has_reliable_pub or has_reliable_upload):
        return "newly_discovered_historical"

    return "unknown"
