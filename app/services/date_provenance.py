from dataclasses import dataclass
from datetime import datetime


@dataclass
class DateProvenanceResult:
    published_at: datetime | None = None
    source_uploaded_at: datetime | None = None
    source_created_at: datetime | None = None
    source_modified_at: datetime | None = None
    repository_pushed_at: datetime | None = None
    source_added_at: datetime | None = None
    precision: str = "unknown"
    confidence: str = "unknown"
    method: str = "unavailable"
    raw_value: str | None = None
    evidence: str | None = None


def map_github_repository(repo: dict) -> DateProvenanceResult:
    created = _parse_iso(repo.get("created_at"))
    updated = _parse_iso(repo.get("updated_at"))
    pushed = _parse_iso(repo.get("pushed_at"))
    return DateProvenanceResult(
        source_created_at=created,
        source_modified_at=updated,
        repository_pushed_at=pushed,
        precision="exact_datetime",
        confidence="authoritative",
        method="source_api",
        raw_value=repo.get("created_at", ""),
        evidence="GitHub API repository created_at/updated_at/pushed_at",
    )


def map_internet_archive(entry: dict) -> DateProvenanceResult:
    publicdate = _parse_iso(entry.get("publicdate"))
    addeddate = _parse_iso(entry.get("addeddate"))
    created = _parse_iso(entry.get("date"))
    updated = _parse_iso(entry.get("updatedate"))
    result = DateProvenanceResult(
        published_at=publicdate,
        source_uploaded_at=addeddate,
        source_added_at=addeddate,
        source_modified_at=updated,
        precision="exact_datetime",
        confidence="authoritative",
        method="source_api",
        evidence="Internet Archive API publicdate/addeddate",
    )
    if created and not publicdate:
        result.source_created_at = created
        result.evidence = "Internet Archive API date/addeddate"
    return result


def map_documentcloud_document(doc: dict) -> DateProvenanceResult:
    created = _parse_iso(doc.get("created_at"))
    updated = _parse_iso(doc.get("updated_at"))
    publish = _parse_iso(doc.get("publish_at"))
    return DateProvenanceResult(
        source_created_at=created,
        source_modified_at=updated,
        published_at=publish,
        precision="exact_datetime",
        confidence="authoritative",
        method="source_api",
        raw_value=doc.get("created_at", ""),
        evidence="DocumentCloud API created_at/publish_at/updated_at",
    )


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
