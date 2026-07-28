from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.country_packs.loader import load_all_country_packs
from app.repositories.claims import ClaimRepository
from app.repositories.sources import SourceRepository
from app.repositories.source_runs import SourceRunRepository
from app.repositories.observations import ObservationRepository
from app.repositories.audit import AuditRepository
from app.schemas.claims import ClaimResponse
from app.schemas.sources import SourceResponse
from app.schemas.source_runs import SourceRunResponse
from app.services.source_runner import run_source, run_enabled_sources
from app.services.source_sync import sync_country_packs_to_database
from app.repositories.source_signals import SourceSignalRepository
from app.schemas.source_signals import SourceSignalResponse

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def raw_feed(
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
async def country_packs_page(request: Request):
    packs = load_all_country_packs()
    templates = request.app.state.templates
    pack_data = []
    for p in packs:
        pack_data.append({
            "country_code": p.country_code,
            "status": p.status,
            "languages": [l.model_dump() for l in (p.languages.languages if p.languages else [])],
            "term_count": len(p.leak_terms.terms) if p.leak_terms else 0,
            "entity_count": len(p.entities.entities) if p.entities else 0,
            "source_count": len(p.sources.sources) if p.sources else 0,
            "errors": p.errors,
        })
    return templates.TemplateResponse(request, "country_packs.html", {"packs": pack_data})


@router.post("/country-packs/sync", response_class=RedirectResponse)
async def sync_packs_web(db: AsyncSession = Depends(get_db)):
    await sync_country_packs_to_database(db)
    await db.commit()
    return RedirectResponse(url="/sources", status_code=303)


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, db: AsyncSession = Depends(get_db)):
    repo = SourceRepository(db)
    sources = await repo.list_sources(limit=500, offset=0)
    items = [SourceResponse.model_validate(s) for s in sources]
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "sources.html", {"sources": items})


@router.post("/sources/{source_id}/run", response_class=RedirectResponse)
async def run_source_web(source_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(source_id)
        await run_source(uid, db)
        await db.commit()
    except Exception:
        await db.rollback()
    return RedirectResponse(url="/sources", status_code=303)


@router.post("/sources/run", response_class=RedirectResponse)
async def run_all_sources_web(
    country_code: str | None = Form(default=None),
    source_type: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    await run_enabled_sources(db, country_code=country_code, source_type=source_type)
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
