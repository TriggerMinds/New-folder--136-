from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.dependencies import get_db
from app.country_packs.loader import load_all_country_packs
from app.repositories.claims import ClaimRepository
from app.repositories.sources import SourceRepository
from app.repositories.source_runs import SourceRunRepository
from app.repositories.observations import ObservationRepository
from app.repositories.audit import AuditRepository
from app.repositories.source_signals import SourceSignalRepository
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository, DistributionObservationRepository
from app.schemas.claims import ClaimResponse
from app.schemas.sources import SourceResponse
from app.schemas.source_runs import SourceRunResponse
from app.schemas.source_signals import SourceSignalResponse
from app.services.source_runner import run_source
from app.services.source_sync import sync_country_packs_to_database
from app.services.dashboard import get_dashboard_summary
from app.database.models.source import Source
from app.database.models.source_run import SourceRun
from app.database.models.artifact_discovery import ArtifactDiscovery
from app.database.models.distribution_observation import DistributionObservation
from app.database.models.reference_observation import ReferenceObservation

router = APIRouter(tags=["web"])


@router.get("/artifacts", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def artifact_feed(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    artifact_type: str | None = Query(default=None),
    host: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = ArtifactDiscoveryRepository(db)
    discoveries = await repo.list_discoveries(limit=limit, offset=offset, artifact_type=artifact_type, host=host)
    total = await repo.count_discoveries()
    dash = await get_dashboard_summary(db)
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "artifacts.html", {
        "discoveries": discoveries, "total": total,
        "limit": limit, "offset": offset,
        "artifact_type": artifact_type or "", "host": host or "",
        "dash": dash,
    })


@router.get("/artifacts/{artifact_id}", response_class=HTMLResponse)
async def artifact_detail_page(request: Request, artifact_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(artifact_id)
    except ValueError:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    repo = ArtifactDiscoveryRepository(db)
    d = await repo.get_discovery(uid)
    if d is None:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    dist_repo = DistributionObservationRepository(db)
    dists = await dist_repo.list_for_artifact(uid)
    refs = []
    if hasattr(repo, "list_references"):
        refs = await repo.list_references(uid)
    acquisitions = []
    if hasattr(repo, "list_acquisitions"):
        acquisitions = await repo.list_acquisitions(uid)
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "artifact_detail.html", {
        "d": d, "distributions": dists, "references": refs, "acquisitions": acquisitions,
    })


@router.get("/distributions", response_class=HTMLResponse)
async def distributions_page(
    request: Request, limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db),
):
    stmt = select(DistributionObservation).order_by(DistributionObservation.observed_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(select(func.count(DistributionObservation.id)))).scalar() or 0
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "distributions.html", {"dists": rows, "total": total})


@router.get("/references", response_class=HTMLResponse)
async def references_page(
    request: Request, limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db),
):
    stmt = select(ReferenceObservation).order_by(ReferenceObservation.observed_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(select(func.count(ReferenceObservation.id)))).scalar() or 0
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "references.html", {"refs": rows, "total": total})


@router.get("/claims", response_class=HTMLResponse)
async def claim_feed(request: Request, limit: int = Query(default=50), offset: int = Query(default=0), db: AsyncSession = Depends(get_db)):
    repo = ClaimRepository(db)
    claims = await repo.list_claims_chronological(limit=limit, offset=offset)
    total = await repo.count_claims()
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "raw_feed.html", {
        "claims": [ClaimResponse.model_validate(c) for c in claims], "total": total,
        "limit": limit, "offset": offset,
    })


@router.get("/claims/{claim_id}", response_class=HTMLResponse)
async def claim_detail_page(request: Request, claim_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(claim_id)
    except ValueError:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    repo = ClaimRepository(db)
    claim = await repo.get_claim(uid)
    if claim is None:
        return HTMLResponse("<h1>404</h1>", status_code=404)
    obs_repo = ObservationRepository(db)
    observations = await obs_repo.list_observations_for_claim(uid)
    audit_repo = AuditRepository(db)
    audit_events = await audit_repo.list_audit_events(claim_id=uid)
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "claim_detail.html", {
        "claim": ClaimResponse.model_validate(claim), "observations": observations, "audit_events": audit_events,
    })


@router.get("/system/health", response_class=HTMLResponse)
async def health_page(request: Request):
    return request.app.state.templates.TemplateResponse(request, "health.html")


@router.get("/country-packs", response_class=HTMLResponse)
async def country_packs_page(request: Request, db: AsyncSession = Depends(get_db)):
    packs = load_all_country_packs()
    templates = request.app.state.templates
    pack_data = []
    for p in packs:
        hc = (await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.lifecycle_status == "historical"))).scalar() or 0
        ac = (await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.lifecycle_status == "active"))).scalar() or 0
        pr = (await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.source_layer == "primary_raw", Source.lifecycle_status == "active"))).scalar() or 0
        rc = (await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.source_layer == "reference_only", Source.present_in_country_pack == True))).scalar() or 0
        pack_data.append({
            "country_code": p.country_code, "status": p.status,
            "source_count": len(p.sources.sources) if p.sources else 0,
            "active_count": ac, "primary_raw_count": pr,
            "reference_only_count": rc, "historical_count": hc,
        })
    return templates.TemplateResponse(request, "country_packs.html", {"packs": pack_data})


@router.post("/country-packs/sync", response_class=RedirectResponse)
async def sync_packs_web(db: AsyncSession = Depends(get_db)):
    await sync_country_packs_to_database(db)
    await db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, view: str | None = Query(default=None), db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    all_sources = await repo.list_sources(limit=500, offset=0)
    active_count = sum(1 for s in all_sources if s.lifecycle_status == "active" and s.present_in_country_pack)
    inactive_count = sum(1 for s in all_sources if s.lifecycle_status == "inactive" and s.present_in_country_pack)
    historical_count = (await db.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "historical"))).scalar() or 0
    if view == "historical":
        sources = [s for s in all_sources if s.lifecycle_status == "historical"]
    else:
        sources = [s for s in all_sources if s.present_in_country_pack]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "sources.html", {
        "sources": [SourceResponse.model_validate(s) for s in sources],
        "historical_view": view == "historical",
        "active_count": active_count, "inactive_count": inactive_count, "historical_count": historical_count,
    })


@router.post("/sources/{source_id}/run", response_class=RedirectResponse)
async def run_source_web(source_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(source_id)
        r = await db.execute(select(Source).where(Source.id == uid))
        src = r.scalar_one_or_none()
        if not src or not (src.enabled and src.lifecycle_status == "active" and src.present_in_country_pack):
            return HTMLResponse("<h1>409</h1><p>Bron is niet actief</p>", status_code=409)
        await run_source(uid, db)
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url="/sources", status_code=303)


@router.post("/sources/run", response_class=RedirectResponse)
async def run_all_active_web(db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.enabled.is_(True), Source.lifecycle_status == "active", Source.present_in_country_pack.is_(True))
    sources = await db.execute(stmt)
    for src in sources.scalars().all():
        try:
            await run_source(src.id, db)
        except Exception:
            pass
    await db.commit()
    return RedirectResponse(url="/source-runs", status_code=303)


@router.get("/source-runs", response_class=HTMLResponse)
async def source_runs_page(
    request: Request, view: str = Query(default="current"),
    limit: int = Query(default=200), offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SourceRun).order_by(SourceRun.started_at.desc()).limit(limit).offset(offset)
    if view == "current":
        subq = select(Source.id).where(Source.present_in_country_pack.is_(True))
        stmt = select(SourceRun).where(SourceRun.source_id.in_(subq)).order_by(SourceRun.started_at.desc()).limit(limit).offset(offset)
    elif view == "historical":
        subq = select(Source.id).where(Source.present_in_country_pack.is_(False))
        stmt = select(SourceRun).where(SourceRun.source_id.in_(subq)).order_by(SourceRun.started_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = len(rows)
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "source_runs.html", {
        "runs": [SourceRunResponse.model_validate(r) for r in rows], "total": total, "view": view,
    })


@router.get("/source-signals", response_class=HTMLResponse)
async def source_signals_page(request: Request, limit: int = Query(default=200), offset: int = Query(default=0), db: AsyncSession = Depends(get_db)):
    repo = SourceSignalRepository(db)
    signals = await repo.list_signals(limit=limit, offset=offset)
    items = [SourceSignalResponse.model_validate(s) for s in signals]
    return request.app.state.templates.TemplateResponse(request, "source_signals.html", {"signals": items})
