from fastapi import APIRouter, Depends, Query
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
    db: AsyncSession = Depends(get_db),
):
    repo = ArtifactDiscoveryRepository(db)
    discoveries = await repo.list_discoveries(limit=limit, offset=offset, artifact_type=artifact_type, host=host)
    total = await repo.count_discoveries()
    return {
        "items": [
            {
                "id": str(d.id),
                "artifact_type": d.artifact_type,
                "locator_type": d.locator_type,
                "original_locator": d.original_locator,
                "host": d.host,
                "title": d.title,
                "filename": d.filename,
                "file_extension": d.file_extension,
                "sha256": d.sha256,
                "ipfs_cid": d.ipfs_cid,
                "magnet_uri": d.magnet_uri,
                "torrent_infohash": d.torrent_infohash,
                "content_length": d.content_length,
                "access_status": d.access_status,
                "acquisition_status": d.acquisition_status,
                "first_observed_at": str(d.first_observed_at),
            }
            for d in discoveries
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
