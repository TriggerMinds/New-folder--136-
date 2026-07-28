"""Tests for freshness classification and date provenance."""
from datetime import datetime, timezone, timedelta
from app.services.freshness import classify_freshness
from app.services.date_provenance import map_github_repository, map_internet_archive

now = datetime.now(timezone.utc)


def test_newly_published():
    pub = now - timedelta(days=5)
    assert classify_freshness(pub, None, None, now) == "newly_published"


def test_newly_uploaded():
    upload = now - timedelta(days=10)
    assert classify_freshness(None, upload, None, now) == "newly_uploaded"


def test_recently_updated():
    mod = now - timedelta(days=15)
    pub = now - timedelta(days=90)
    assert classify_freshness(pub, None, mod, now) == "recently_updated"


def test_newly_discovered_historical():
    pub = now - timedelta(days=365)
    assert classify_freshness(pub, None, None, now) == "newly_discovered_historical"


def test_unknown():
    assert classify_freshness(None, None, None, now) == "unknown"


def test_freshness_window_boundary():
    pub = now - timedelta(days=29)
    assert classify_freshness(pub, None, None, now) == "newly_published"
    pub2 = now - timedelta(days=31)
    assert classify_freshness(pub2, None, None, now) == "newly_discovered_historical"


def test_github_date_mapping():
    repo = {
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2026-07-20T12:00:00Z",
        "pushed_at": "2026-07-28T08:00:00Z",
    }
    dp = map_github_repository(repo)
    assert dp.published_at is None
    assert dp.source_created_at is not None
    assert dp.source_modified_at is not None
    assert dp.repository_pushed_at is not None
    assert dp.precision == "exact_datetime"
    assert dp.confidence == "authoritative"
    assert dp.method == "source_api"


def test_archive_date_mapping():
    entry = {
        "publicdate": "2026-07-01T12:00:00Z",
        "addeddate": "2026-07-28T10:00:00Z",
        "date": "2026-06-15",
        "updatedate": "2026-07-29T08:00:00Z",
    }
    dp = map_internet_archive(entry)
    assert dp.published_at is not None
    assert dp.source_uploaded_at is not None
    assert dp.source_added_at is not None
    assert dp.source_modified_at is not None
    assert dp.confidence == "authoritative"


def test_archive_no_dates():
    dp = map_internet_archive({})
    assert dp.published_at is None
    assert dp.source_uploaded_at is None
    assert dp.source_added_at is None


def test_github_no_published_at():
    """GitHub created_at must NEVER become published_at."""
    repo = {"created_at": "2024-01-01T00:00:00Z"}
    dp = map_github_repository(repo)
    assert dp.published_at is None


def test_first_observed_not_upload():
    """first_observed_at must never be used as upload date."""
    d = now - timedelta(hours=1)
    assert classify_freshness(None, None, None, d) == "unknown"
