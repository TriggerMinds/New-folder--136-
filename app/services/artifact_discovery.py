from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from app.repositories.artifact_discoveries import DistributionObservationRepository
from app.services.url_normalization import normalize_url

ARCHIVE_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".json", ".xml", ".zip", ".7z", ".tar", ".gz", ".tgz", ".rar", ".eml", ".mbox", ".sql", ".dump", ".pst", ".ost"}


class ArtifactRegistrationResult:
    def __init__(self):
        self.artifact: ArtifactDiscovery | None = None
        self.is_new: bool = False
        self.deduplication_type: str | None = None
        self.distribution_created: bool = False


def _classify(url: str, metadata: dict) -> tuple:
    raw = metadata or {}
    ext = (raw.get("file_extension", "") or "").lower()
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    fname = path.split("/")[-1] if path else ""
    _, file_ext = fname.rsplit(".", 1) if "." in fname else ("", "")
    file_ext = "." + file_ext.lower() if file_ext else ext
    tmap = {".pdf": "document", ".doc": "document", ".docx": "document",
            ".xls": "dataset", ".xlsx": "dataset", ".csv": "dataset", ".json": "dataset", ".xml": "dataset",
            ".zip": "archive_file", ".7z": "archive_file", ".tar": "archive_file", ".gz": "archive_file",
            ".tgz": "archive_file", ".rar": "archive_file",
            ".eml": "email_archive", ".mbox": "email_archive",
            ".sql": "database_dump", ".dump": "database_dump", ".pst": "email_archive", ".ost": "email_archive"}
    atype = tmap.get(file_ext, "document") if file_ext in ARCHIVE_EXTS else "unknown"
    ltype = "direct_url"
    if raw.get("magnet_uri"): ltype = "magnet"
    elif raw.get("ipfs_cid"): ltype = "ipfs_cid"
    elif raw.get("torrent_infohash"): ltype = "torrent_hash"
    elif raw.get("repository_url"): ltype = "repository"
    return atype, ltype, file_ext, fname


async def register_artifact_discovery(
    session: AsyncSession, source_id: object, url: str,
    title: str | None = None, description: str | None = None,
    raw_metadata: dict | None = None, source_run_id: object | None = None,
) -> ArtifactRegistrationResult:
    repo = ArtifactDiscoveryRepository(session)
    dist_repo = DistributionObservationRepository(session)
    rm = raw_metadata or {}
    canonical = normalize_url(url)
    host = urlparse(canonical).hostname or "unknown"
    sha256 = rm.get("sha256")
    torrent_hash = rm.get("torrent_infohash") or rm.get("torrent_ih")
    ipfs_cid = rm.get("ipfs_cid")
    repo_url = rm.get("repository_url")
    repo_ref = rm.get("repository_ref")
    archive_id = rm.get("archive_identifier")
    fname = rm.get("filename", "")

    existing = None
    dedup_type = None

    if sha256:
        existing = await repo.find_by_sha256(sha256)
        if existing: dedup_type = "sha256"
    if not existing and torrent_hash:
        existing = await repo.find_by_torrent_infohash(torrent_hash)
        if existing: dedup_type = "torrent_infohash"
    if not existing and ipfs_cid:
        existing = await repo.find_by_ipfs_cid(ipfs_cid)
        if existing: dedup_type = "ipfs_cid"
    if not existing and repo_url and repo_ref:
        existing = await repo.find_by_repository(repo_url, repo_ref)
        if existing: dedup_type = "repository"
    if not existing and archive_id:
        existing = await repo.find_by_archive_identifier(archive_id)
        if existing: dedup_type = "archive_identifier"
    if not existing:
        existing = await repo.find_by_canonical_locator(canonical)
        if existing: dedup_type = "canonical_locator"
    if not existing and fname and host:
        existing = await repo.find_by_weak_fingerprint(fname, host)
        if existing: dedup_type = "weak_fingerprint"

    result = ArtifactRegistrationResult()

    if existing:
        existing.last_observed_at = datetime.now(timezone.utc)
        if title and not existing.title: existing.title = title
        if description and not existing.description: existing.description = description
        await repo.update_discovery(existing)
        result.artifact = existing
        result.is_new = False
        result.deduplication_type = dedup_type

        dist_exists = await dist_repo.exists(existing.id, source_id, canonical)
        if not dist_exists:
            dist = DistributionObservation(
                artifact_discovery_id=existing.id, source_id=source_id,
                observed_at=datetime.now(timezone.utc),
                locator=url, canonical_locator=canonical,
                distribution_type="origin_candidate", title=title,
                raw_metadata={"discovery_source": "primary_raw", "host": host},
            )
            await dist_repo.create_observation(dist)
            result.distribution_created = True
        return result

    atype, ltype, file_ext, fname2 = _classify(url, rm)
    now = datetime.now(timezone.utc)
    discovery = ArtifactDiscovery(
        first_observed_at=now, last_observed_at=now,
        source_id=source_id, source_run_id=source_run_id,
        artifact_type=atype, locator_type=ltype,
        original_locator=url, canonical_locator=canonical,
        host=host, title=title, description=description,
        filename=fname or fname2 or None,
        file_extension=file_ext or None,
        sha256=sha256, torrent_infohash=torrent_hash,
        ipfs_cid=ipfs_cid, repository_url=repo_url,
        repository_ref=repo_ref, archive_identifier=archive_id,
        raw_metadata=rm,
        access_status="observed", acquisition_status="metadata_only",
        analysis_status="not_started",
    )
    created = await repo.create_discovery(discovery)
    dist = DistributionObservation(
        artifact_discovery_id=created.id, source_id=source_id,
        observed_at=now, locator=url, canonical_locator=canonical,
        distribution_type="origin_candidate", title=title,
        raw_metadata={"discovery_source": "primary_raw", "host": host},
    )
    await dist_repo.create_observation(dist)
    result.artifact = created
    result.is_new = True
    result.distribution_created = True
    return result
