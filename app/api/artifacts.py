from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("")
async def list_artifacts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    artifact_type: str | None = Query(default=None),
    host: str | None = Query(default=None),
    q: str | None = Query(default=None),
    file_extension: str | None = Query(default=None),
    locator_type: str | None = Query(default=None),
    access_status: str | None = Query(default=None),
    acquisition_status: str | None = Query(default=None),
    include_invalidated: bool = Query(default=False),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort: str = Query(default="first_observed_desc"),
    db: AsyncSession = Depends(get_db),
):
    repo = ArtifactDiscoveryRepository(db)
    items = await repo.list_discoveries(
        limit=limit, offset=offset, artifact_type=artifact_type, host=host,
        q=q, file_extension=file_extension, locator_type=locator_type,
        access_status=access_status, acquisition_status=acquisition_status,
        include_invalidated=include_invalidated,
        date_from=date_from, date_to=date_to, sort=sort,
    )
    total = await repo.count_discoveries(include_invalidated=include_invalidated)
    return {"items": [_ad_json(d) for d in items], "total": total, "limit": limit, "offset": offset}


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = ArtifactDiscoveryRepository(db)
    d = await repo.get_discovery(artifact_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Artifact niet gevonden")
    data = _ad_json(d)
    data["distribution_count"] = await repo.count_distributions(artifact_id)
    data["reference_count"] = await repo.count_references(artifact_id)
    data["acquisition_count"] = await repo.count_acquisitions(artifact_id)
    return data


@router.get("/{artifact_id}/distributions")
async def list_artifact_distributions(
    artifact_id: UUID, limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db),
):
    repo = ArtifactDiscoveryRepository(db)
    if await repo.get_discovery(artifact_id) is None:
        raise HTTPException(status_code=404, detail="Artifact niet gevonden")
    dists = await repo.list_distributions(artifact_id, limit=limit, offset=offset)
    total = await repo.count_distributions(artifact_id)
    return {"items": [_dist_json(d) for d in dists], "total": total, "limit": limit, "offset": offset}


@router.get("/{artifact_id}/references")
async def list_artifact_references(
    artifact_id: UUID, limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db),
):
    repo = ArtifactDiscoveryRepository(db)
    if await repo.get_discovery(artifact_id) is None:
        raise HTTPException(status_code=404, detail="Artifact niet gevonden")
    refs = await repo.list_references(artifact_id, limit=limit, offset=offset)
    total = await repo.count_references(artifact_id)
    return {"items": [_ref_json(r) for r in refs], "total": total, "limit": limit, "offset": offset}


@router.get("/{artifact_id}/download-status")
async def download_status(artifact_id: UUID, limit: int = Query(default=10, ge=1, le=100),
                           offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db)):
    repo = ArtifactDiscoveryRepository(db)
    d = await repo.get_discovery(artifact_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Artifact niet gevonden")
    acqs = await repo.list_acquisitions(artifact_id, limit=limit, offset=offset)
    total = await repo.count_acquisitions(artifact_id)
    return {
        "artifact_id": str(artifact_id),
        "acquisition_status": d.acquisition_status,
        "access_status": d.access_status,
        "acquisitions": [_acq_json(a) for a in acqs],
        "total": total, "limit": limit, "offset": offset,
    }


@router.post("/{artifact_id}/download")
async def trigger_download(artifact_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.config import settings
    from app.database.models.artifact_acquisition import ArtifactAcquisition
    from datetime import datetime, timezone
    repo = ArtifactDiscoveryRepository(db)
    d = await repo.get_discovery(artifact_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Artifact niet gevonden")
    if not settings.download_artifacts:
        acq = ArtifactAcquisition(
            artifact_discovery_id=artifact_id,
            requested_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="blocked_by_configuration",
            requested_locator=d.canonical_locator,
            downloaded_bytes=0,
            error="artifact downloads are disabled by configuration",
        )
        db.add(acq)
        await db.flush()
        await db.commit()
        raise HTTPException(status_code=409, detail=f"Artifact downloads disabled by configuration. Acquisition {acq.id} logged as blocked_by_configuration.")
    raise HTTPException(status_code=501, detail="Download enabled implementation pending")


def _ad_json(d):
    return {
        "id": str(d.id), "artifact_type": d.artifact_type, "locator_type": d.locator_type,
        "original_locator": d.original_locator, "canonical_locator": d.canonical_locator,
        "host": d.host, "title": d.title, "filename": d.filename,
        "file_extension": d.file_extension, "sha256": d.sha256,
        "ipfs_cid": d.ipfs_cid, "magnet_uri": d.magnet_uri,
        "torrent_infohash": d.torrent_infohash, "content_length": d.content_length,
        "access_status": d.access_status, "acquisition_status": d.acquisition_status,
        "first_observed_at": str(d.first_observed_at),
    }


def _dist_json(d):
    return {"id": str(d.id), "artifact_discovery_id": str(d.artifact_discovery_id),
            "source_id": str(d.source_id), "distribution_type": d.distribution_type,
            "locator": d.locator, "observed_at": str(d.observed_at)}


def _ref_json(r):
    return {"id": str(r.id), "artifact_discovery_id": str(r.artifact_discovery_id) if r.artifact_discovery_id else None,
            "claim_id": str(r.claim_id) if r.claim_id else None, "source_id": str(r.source_id),
            "reference_type": r.reference_type, "title": r.title, "url": r.url,
            "observed_at": str(r.observed_at)}


def _acq_json(a):
    return {"id": str(a.id), "status": a.status, "requested_at": str(a.requested_at),
            "completed_at": str(a.completed_at) if a.completed_at else None,
            "downloaded_bytes": a.downloaded_bytes, "error": a.error}
