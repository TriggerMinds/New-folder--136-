from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.artifact_discoveries import DistributionObservationRepository

router = APIRouter(prefix="/api/distribution-observations", tags=["distribution-observations"])


@router.get("")
async def list_distributions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    artifact_id: UUID | None = Query(default=None),
    source_id: UUID | None = Query(default=None),
    distribution_type: str | None = Query(default=None),
    host: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = DistributionObservationRepository(db)
    items = await repo.list_all(limit=limit, offset=offset, artifact_id=artifact_id,
                                 source_id=source_id, distribution_type=distribution_type,
                                 host=host, date_from=date_from, date_to=date_to)
    total = await repo.count_all(artifact_id=artifact_id, source_id=source_id,
                                  distribution_type=distribution_type, host=host,
                                  date_from=date_from, date_to=date_to)
    return {"items": [{"id": str(d.id), "artifact_discovery_id": str(d.artifact_discovery_id),
                        "source_id": str(d.source_id), "distribution_type": d.distribution_type,
                        "locator": d.locator, "canonical_locator": d.canonical_locator,
                        "title": d.title, "observed_at": str(d.observed_at)} for d in items],
            "total": total, "limit": limit, "offset": offset}
