from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from app.repositories.artifact_discoveries import DistributionObservationRepository
from app.services.url_normalization import normalize_url


ARCHIVE_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".json", ".xml", ".zip", ".7z", ".tar", ".gz", ".tgz", ".rar", ".eml", ".mbox", ".sql", ".dump", ".pst", ".ost"}

MAGNET_PREFIX = "magnet:"
IPFS_CIDV0_PREFIX = "Qm"
IPFS_CIDV1_PREFIX = "bafy"
TORRENT_HASH_LEN = 40


def _classify_artifact(url: str, metadata: dict) -> tuple[str, str, str, str, str]:
    raw = metadata or {}
    ext = raw.get("file_extension", "")
    magnet = raw.get("magnet_uri", "")
    ipfs = raw.get("ipfs_cid", "")
    torhash = raw.get("torrent_infohash", "")
    repo = raw.get("repository_url", "")

    if magnet:
        return "unknown", "magnet", "", "", ""
    if ipfs:
        return "ipfs_object", "ipfs_cid", "", "", ""
    if torhash:
        return "unknown", "torrent_hash", "", "", ""
    if repo:
        return "source_code", "repository", "", "", ""

    ext = ext.lower() if ext else ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    fname = path.split("/")[-1] if path else ""
    _, file_ext = fname.rsplit(".", 1) if "." in fname else ("", "")

    file_ext = "." + file_ext.lower() if file_ext else ext

    if file_ext in ARCHIVE_EXTS:
        artifact_type = {
            ".pdf": "document",
            ".doc": "document", ".docx": "document",
            ".xls": "dataset", ".xlsx": "dataset",
            ".csv": "dataset", ".json": "dataset", ".xml": "dataset",
            ".zip": "archive_file", ".7z": "archive_file",
            ".tar": "archive_file", ".gz": "archive_file",
            ".tgz": "archive_file", ".rar": "archive_file",
            ".eml": "email_archive", ".mbox": "email_archive",
            ".sql": "database_dump", ".dump": "database_dump",
            ".pst": "email_archive", ".ost": "email_archive",
        }.get(file_ext, "document")
        return artifact_type, "direct_url", file_ext, fname, ""

    return "unknown", "direct_url", file_ext or "", fname, ""


async def register_artifact_discovery(
    session: AsyncSession,
    source_id: object,
    url: str,
    title: str | None = None,
    description: str | None = None,
    raw_metadata: dict | None = None,
    source_run_id: object | None = None,
) -> ArtifactDiscovery:
    repo = ArtifactDiscoveryRepository(session)
    dist_repo = DistributionObservationRepository(session)

    canonical = normalize_url(url)
    host = urlparse(canonical).hostname or "unknown"

    artifact_type, locator_type, file_ext, fname, _ = _classify_artifact(url, raw_metadata)

    now = datetime.now(timezone.utc)

    discovery = ArtifactDiscovery(
        first_observed_at=now,
        last_observed_at=now,
        source_id=source_id,
        source_run_id=source_run_id,
        artifact_type=artifact_type,
        locator_type=locator_type,
        original_locator=url,
        canonical_locator=canonical,
        host=host,
        title=title,
        description=description,
        filename=fname or None,
        file_extension=file_ext or None,
        raw_metadata=raw_metadata or {},
        access_status="observed",
        acquisition_status="metadata_only",
        analysis_status="not_started",
    )

    created = await repo.create_discovery(discovery)

    dist = DistributionObservation(
        artifact_discovery_id=created.id,
        source_id=source_id,
        observed_at=now,
        locator=url,
        canonical_locator=canonical,
        distribution_type="origin_candidate",
        title=title,
        raw_metadata={"discovery_source": "primary_raw", "host": host},
    )
    await dist_repo.create_observation(dist)

    return created
