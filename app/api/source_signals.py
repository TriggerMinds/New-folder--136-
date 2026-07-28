from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.source_signals import SourceSignalRepository
from app.repositories.claims import ClaimRepository
from app.schemas.source_signals import SourceSignalResponse, SourceSignalListResponse
from app.database.models.source_signal import SourceSignal

router = APIRouter(prefix="/api/source-signals", tags=["source-signals"])


@router.get("", response_model=SourceSignalListResponse)
async def list_signals(
    processing_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceSignalRepository(db)
    signals = await repo.list_signals(
        processing_status=processing_status,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_signals(processing_status=processing_status)
    items = [SourceSignalResponse.model_validate(s).model_dump(mode="json") for s in signals]
    return SourceSignalListResponse(items=items, total=total)


@router.get("/{signal_id}", response_model=SourceSignalResponse)
async def get_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = SourceSignalRepository(db)
    signal = await repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signaal niet gevonden")
    return SourceSignalResponse.model_validate(signal)


@router.post("/{signal_id}/resolve")
async def resolve_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = SourceSignalRepository(db)
    signal = await repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signaal niet gevonden")
    signal.processing_status = "no_origin_found"
    await repo.update_signal(signal)
    await db.commit()
    return {"status": "resolved", "processing_status": "no_origin_found"}


@router.post("/{signal_id}/link/{claim_id}")
async def link_signal_to_claim(
    signal_id: UUID,
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    signal_repo = SourceSignalRepository(db)
    claim_repo = ClaimRepository(db)
    signal = await signal_repo.get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signaal niet gevonden")
    claim = await claim_repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    signal.linked_claim_id = claim_id
    signal.processing_status = "linked_to_claim"
    await signal_repo.update_signal(signal)
    await db.commit()
    return {"status": "linked", "signal_id": str(signal_id), "claim_id": str(claim_id)}
