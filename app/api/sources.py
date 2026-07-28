from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.source import Source
from app.repositories.sources import SourceRepository
from app.repositories.source_runs import SourceRunRepository
from app.schemas.sources import SourceCreate, SourceResponse, SourceListResponse
from app.schemas.source_runs import SourceRunListResponse, SourceRunResponse
from app.services.source_runner import run_source, run_enabled_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    source = Source(
        external_id=payload.external_id,
        name=payload.name,
        country_code=payload.country_code,
        languages=payload.languages,
        source_type=payload.source_type,
        base_url=payload.base_url,
        poll_url=payload.poll_url,
        enabled=payload.enabled,
        poll_interval_minutes=payload.poll_interval_minutes,
    )
    created = await repo.create_source(source)
    return SourceResponse.model_validate(created)


@router.get("", response_model=SourceListResponse)
async def list_sources(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    enabled_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    sources = await repo.list_sources(limit=limit, offset=offset, enabled_only=enabled_only)
    total = await repo.count_sources(enabled_only=enabled_only)
    items = [SourceResponse.model_validate(s).model_dump(mode="json") for s in sources]
    return SourceListResponse(items=items, total=total)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    source = await repo.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Bron niet gevonden")
    return SourceResponse.model_validate(source)


@router.post("/{source_id}/run")
async def run_single_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await run_source(source_id, db)
    await db.commit()
    return {
        "source_id": str(result.source_id) if result.source_id else None,
        "source_external_id": result.source_external_id,
        "success": result.success,
        "items_seen": result.items_seen,
        "items_matched": result.items_matched,
        "claims_created": result.claims_created,
        "claims_deduplicated": result.claims_deduplicated,
        "error": result.error,
    }


@router.post("/run")
async def run_all_sources(
    country_code: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    batch = await run_enabled_sources(db, country_code=country_code, source_type=source_type)
    await db.commit()
    return {
        "total_sources": batch.total_sources,
        "successful": batch.successful,
        "failed": batch.failed,
        "results": [
            {
                "source_id": str(r.source_id) if r.source_id else None,
                "source_external_id": r.source_external_id,
                "success": r.success,
                "items_seen": r.items_seen,
                "items_matched": r.items_matched,
                "claims_created": r.claims_created,
                "claims_deduplicated": r.claims_deduplicated,
                "error": r.error,
            }
            for r in batch.results
        ],
    }


@router.get("/{source_id}/runs", response_model=SourceRunListResponse)
async def list_source_runs(
    source_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    source = await repo.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Bron niet gevonden")
    run_repo = SourceRunRepository(db)
    runs = await run_repo.list_runs(source_id=source_id, limit=limit, offset=offset)
    total = await run_repo.count_runs(source_id=source_id)
    items = [SourceRunResponse.model_validate(r).model_dump(mode="json") for r in runs]
    return SourceRunListResponse(items=items, total=total)
