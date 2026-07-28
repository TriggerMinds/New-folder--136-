from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.reference_observation import ReferenceObservation

router = APIRouter(prefix="/api/reference-observations", tags=["reference-observations"])


@router.get("")
async def list_references(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    artifact_id: UUID | None = Query(default=None),
    claim_id: UUID | None = Query(default=None),
    source_id: UUID | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ReferenceObservation)
    if artifact_id:
        stmt = stmt.where(ReferenceObservation.artifact_discovery_id == artifact_id)
    if claim_id:
        stmt = stmt.where(ReferenceObservation.claim_id == claim_id)
    if source_id:
        stmt = stmt.where(ReferenceObservation.source_id == source_id)
    if reference_type:
        stmt = stmt.where(ReferenceObservation.reference_type == reference_type)
    if date_from:
        stmt = stmt.where(ReferenceObservation.observed_at >= date_from)
    if date_to:
        stmt = stmt.where(ReferenceObservation.observed_at <= date_to)
    stmt = stmt.order_by(ReferenceObservation.observed_at.desc()).limit(limit).offset(offset)
    r = await db.execute(stmt)
    items = r.scalars().all()
    total_r = await db.execute(select(func.count(ReferenceObservation.id)))
    total = total_r.scalar() or 0
    return {"items": [{"id": str(i.id), "artifact_discovery_id": str(i.artifact_discovery_id) if i.artifact_discovery_id else None,
                        "claim_id": str(i.claim_id) if i.claim_id else None, "source_id": str(i.source_id),
                        "reference_type": i.reference_type, "title": i.title, "url": i.url,
                        "observed_at": str(i.observed_at)} for i in items],
            "total": total, "limit": limit, "offset": offset}
