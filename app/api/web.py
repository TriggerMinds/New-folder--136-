from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Form
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
from app.repositories.artifact_discoveries import ArtifactDiscoveryRepository
from app.schemas.claims import ClaimResponse
from app.schemas.sources import SourceResponse
from app.schemas.source_runs import SourceRunResponse
from app.schemas.source_signals import SourceSignalResponse
from app.services.source_runner import run_source, run_enabled_sources
from app.services.source_sync import sync_country_packs_to_database
from app.database.models.source import Source

router = APIRouter(tags=["web"])


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
    src_count = await db.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "active", Source.source_layer == "primary_raw"))
    sources_active = src_count.scalar() or 0
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "artifacts.html", {
        "discoveries": discoveries, "total": total,
        "limit": limit, "offset": offset,
        "artifact_type": artifact_type or "", "host": host or "",
        "metadata_only": total, "sources_active": sources_active,
    })


@router.get("/claims", response_class=HTMLResponse)
async def claim_feed(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    country: str | None = Query(default=None),
    language: str | None = Query(default=None),
    host: str | None = Query(default=None),
    dossier: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = ClaimRepository(db)
    claims = await repo.list_claims_chronological(
        limit=limit, offset=offset, country=country, language=language,
        host=host, dossier=dossier, date_from=date_from, date_to=date_to,
    )
    total = await repo.count_claims(
        country=country, language=language, host=host,
        dossier=dossier, date_from=date_from, date_to=date_to,
    )
    items = [ClaimResponse.model_validate(c) for c in claims]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "raw_feed.html", {
        "claims": items, "total": total, "limit": limit, "offset": offset,
        "country": country or "", "language": language or "", "host": host or "",
        "dossier": dossier or "", "date_from": date_from or "", "date_to": date_to or "",
    })


@router.get("/claims/{claim_id}", response_class=HTMLResponse)
async def claim_detail(request: Request, claim_id: str, db: AsyncSession = Depends(get_db)):
    repo = ClaimRepository(db)
    try:
        uid = UUID(claim_id)
    except ValueError:
        return HTMLResponse(content="<h1>404</h1><p>Claim niet gevonden</p>", status_code=404)
    claim = await repo.get_claim(uid)
    if claim is None:
        return HTMLResponse(content="<h1>404</h1><p>Claim niet gevonden</p>", status_code=404)
    obs_repo = ObservationRepository(db)
    observations = await obs_repo.list_observations_for_claim(uid)
    audit_repo = AuditRepository(db)
    audit_events = await audit_repo.list_audit_events(claim_id=uid)
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "claim_detail.html", {
        "claim": ClaimResponse.model_validate(claim),
        "observations": observations,
        "audit_events": audit_events,
    })


@router.get("/system/health", response_class=HTMLResponse)
async def health_page(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "health.html")


@router.get("/country-packs", response_class=HTMLResponse)
async def country_packs_page(request: Request, db: AsyncSession = Depends(get_db)):
    packs = load_all_country_packs()
    historical_counts = {}
    for p in packs:
        cnt = await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.lifecycle_status == "historical"))
        historical_counts[p.country_code] = cnt.scalar() or 0
    active_counts = {}
    for p in packs:
        cnt = await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.lifecycle_status == "active"))
        active_counts[p.country_code] = cnt.scalar() or 0
    primary_raw_counts = {}
    for p in packs:
        cnt = await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.source_layer == "primary_raw", Source.lifecycle_status == "active"))
        primary_raw_counts[p.country_code] = cnt.scalar() or 0
    reference_counts = {}
    for p in packs:
        cnt = await db.execute(select(func.count(Source.id)).where(Source.country_code == p.country_code, Source.source_layer == "reference_only", Source.present_in_country_pack == True))
        reference_counts[p.country_code] = cnt.scalar() or 0
    templates = request.app.state.templates
    pack_data = []
    for p in packs:
        pack_data.append({
            "country_code": p.country_code,
            "status": p.status,
            "source_count": len(p.sources.sources) if p.sources else 0,
            "active_count": active_counts.get(p.country_code, 0),
            "primary_raw_count": primary_raw_counts.get(p.country_code, 0),
            "reference_only_count": reference_counts.get(p.country_code, 0),
            "historical_count": historical_counts.get(p.country_code, 0),
        })
    return templates.TemplateResponse(request, "country_packs.html", {"packs": pack_data})


@router.post("/country-packs/sync", response_class=RedirectResponse)
async def sync_packs_web(db: AsyncSession = Depends(get_db)):
    await sync_country_packs_to_database(db)
    await db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(
    request: Request,
    view: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRepository(db)
    historical_view = view == "historical"
    all_sources = await repo.list_sources(limit=500, offset=0)
    active_count = sum(1 for s in all_sources if s.lifecycle_status == "active" and s.present_in_country_pack)
    inactive_count = sum(1 for s in all_sources if s.lifecycle_status == "inactive" and s.present_in_country_pack)
    historical_count = sum(1 for s in all_sources if s.lifecycle_status == "historical")
    if historical_view:
        sources = [s for s in all_sources if s.lifecycle_status == "historical"]
    else:
        sources = [s for s in all_sources if s.present_in_country_pack]
    items = [SourceResponse.model_validate(s) for s in sources]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "sources.html", {
        "sources": items, "historical_view": historical_view,
        "active_count": active_count, "inactive_count": inactive_count,
        "historical_count": historical_count,
    })


@router.post("/sources/{source_id}/run", response_class=RedirectResponse)
async def run_source_web(source_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(source_id)
        from sqlalchemy import select as _select
        result = await db.execute(_select(Source).where(Source.id == uid))
        src = result.scalar_one_or_none()
        if src and not (src.enabled and src.lifecycle_status == "active" and src.present_in_country_pack):
            return HTMLResponse(content="<h1>409</h1><p>Bron is niet actief</p>", status_code=409)
        await run_source(uid, db)
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url="/sources", status_code=303)


@router.post("/sources/run", response_class=RedirectResponse)
async def run_all_active_sources_web(db: AsyncSession = Depends(get_db)):
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
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRunRepository(db)
    runs = await repo.list_runs(limit=limit, offset=offset)
    items = [SourceRunResponse.model_validate(r) for r in runs]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "source_runs.html", {"runs": items})


@router.get("/source-signals", response_class=HTMLResponse)
async def source_signals_page(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceSignalRepository(db)
    signals = await repo.list_signals(limit=limit, offset=offset)
    items = [SourceSignalResponse.model_validate(s) for s in signals]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "source_signals.html", {"signals": items})
