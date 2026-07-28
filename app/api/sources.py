from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.database.models.source import Source
from app.repositories.sources import SourceRepository
from app.repositories.source_runs import SourceRunRepository
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from app.schemas.sources import SourceCreate, SourceResponse, SourceListResponse
from app.schemas.source_runs import SourceRunListResponse, SourceRunResponse
from app.services.source_runner import run_source, run_enabled_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/summary")
async def source_summary(db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    return await repo.get_summary()


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    source = Source(
        external_id=payload.external_id, name=payload.name,
        country_code=payload.country_code, languages=payload.languages,
        source_type=payload.source_type, base_url=payload.base_url,
        poll_url=payload.poll_url, enabled=payload.enabled,
        poll_interval_minutes=payload.poll_interval_minutes,
    )
    return SourceResponse.model_validate(await repo.create_source(source))


@router.get("", response_model=SourceListResponse)
async def list_sources(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    enabled_only: bool = Query(default=False),
    lifecycle_status: str | None = Query(default=None),
    source_layer: str | None = Query(default=None),
    include_historical: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    sources = await repo.list_sources(
        limit=limit, offset=offset, enabled_only=enabled_only,
        lifecycle_status=lifecycle_status, source_layer=source_layer,
        include_historical=include_historical,
    )
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


@router.get("/{source_id}/stats")
async def source_stats(source_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
    from app.repositories.source_runs import SourceRunRepository
    from app.repositories.sources import SourceRepository
    repo = SourceRepository(db)
    source = await repo.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Bron niet gevonden")
    run_repo = SourceRunRepository(db)
    art_repo = ArtifactDiscoveryRepository(db)
    runs_total = await run_repo.count_runs(source_id=source_id)
    runs_all = await run_repo.list_runs(source_id=source_id, limit=999999, offset=0)
    runs_success = sum(1 for r in runs_all if r.success)
    runs_failed = sum(1 for r in runs_all if not r.success)
    artifacts_total = await art_repo.count_artifacts_for_source(source_id)
    return {
        "runs_total": runs_total,
        "runs_success": runs_success,
        "runs_failed": runs_failed,
        "artifacts_total": artifacts_total,
    }


@router.post("/{source_id}/run")
async def run_single_source(source_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    source = await repo.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Bron niet gevonden")
    if not (source.enabled and source.lifecycle_status == "active" and source.present_in_country_pack):
        raise HTTPException(status_code=409, detail="Bron is niet actief of niet aanwezig in country pack")
    result = await run_source(source_id, db)
    await db.commit()
    return {
        "source_id": str(result.source_id) if result.source_id else None,
        "source_external_id": result.source_external_id,
        "success": result.success,
        "items_seen": result.items_seen,
        "artifact_items_seen": result.artifact_items_seen,
        "claims_created": result.claims_created,
        "signals_created": result.signals_created,
        "error": result.error,
    }


@router.post("/run")
async def run_all_sources(
    country_code: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select as _select
    stmt = _select(Source).where(Source.enabled.is_(True), Source.lifecycle_status == "active", Source.present_in_country_pack.is_(True))
    if country_code:
        stmt = stmt.where(Source.country_code == country_code)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    sources = await db.execute(stmt)
    results = []
    for src in sources.scalars().all():
        try:
            r = await run_source(src.id, db)
            results.append({
                "source_id": str(r.source_id), "source_external_id": r.source_external_id,
                "success": r.success, "items_seen": r.items_seen,
                "artifact_items_seen": r.artifact_items_seen,
                "error": r.error,
            })
        except Exception as e:
            results.append({"source_id": str(src.id), "success": False, "error": str(e)})
    await db.commit()
    return {"results": results, "total": len(results), "successful": sum(1 for r in results if r.get("success")), "failed": sum(1 for r in results if not r.get("success"))}


@router.get("/{source_id}/runs", response_model=SourceRunListResponse)
async def list_source_runs(source_id: UUID, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    if await repo.get_source(source_id) is None:
        raise HTTPException(status_code=404, detail="Bron niet gevonden")
    run_repo = SourceRunRepository(db)
    runs = await run_repo.list_runs(source_id=source_id, limit=limit, offset=offset)
    total = await run_repo.count_runs(source_id=source_id)
    items = [SourceRunResponse.model_validate(r).model_dump(mode="json") for r in runs]
    return SourceRunListResponse(items=items, total=total)
