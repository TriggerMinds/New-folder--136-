from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.audit import AuditRepository
from app.repositories.claims import ClaimRepository
from app.repositories.sources import SourceRepository
from app.schemas.audit import AuditEventListResponse, AuditEventResponse
from app.services.audit import append_audit_event

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=AuditEventListResponse)
async def list_audit_events(
    claim_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    if claim_id is not None:
        claim_repo = ClaimRepository(db)
        claim = await claim_repo.get_claim(claim_id)
        if claim is None:
            raise HTTPException(status_code=404, detail="Claim niet gevonden")
    repo = AuditRepository(db)
    events = await repo.list_audit_events(claim_id=claim_id, limit=limit, offset=offset)
    total = await repo.count_audit_events(claim_id=claim_id)
    items = [AuditEventResponse.model_validate(e).model_dump(mode="json") for e in events]
    return AuditEventListResponse(items=items, total=total)
