from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.claims import ClaimRepository
from app.repositories.observations import ObservationRepository
from app.repositories.audit import AuditRepository
from app.schemas.claims import ClaimCreate, ClaimResponse, ClaimListResponse, ClaimUpdate
from app.schemas.observations import ObservationListResponse, ObservationResponse
from app.schemas.audit import AuditEventListResponse, AuditEventResponse
from app.services.claim_registration import register_observed_leak_claim

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.post("/register", response_model=dict)
async def register_claim(
    payload: ClaimCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await register_observed_leak_claim(
        session=db,
        title_original=payload.title_original,
        first_observed_url=payload.first_observed_url,
        source_language=payload.source_language,
        summary=payload.summary,
        claim_text=payload.claim_text,
        countries=payload.countries,
        eu_entities=payload.eu_entities,
        national_entities=payload.national_entities,
        dossiers=payload.dossiers,
        earliest_known_public_url=payload.earliest_known_public_url,
        claimed_origin_url=payload.claimed_origin_url,
        confirmed_origin_url=payload.confirmed_origin_url,
        title_translated=payload.title_translated,
        discovery_method=payload.discovery_method,
        connector_type=payload.connector_type,
        connector_version=payload.connector_version,
        http_status=payload.http_status,
        content_excerpt=payload.content_excerpt,
        content_hash_sha256=payload.content_hash_sha256,
        observed_at=payload.observed_at,
        source_id=None,
    )
    claim_data = ClaimResponse.model_validate(result.claim)
    return {
        "claim": claim_data.model_dump(mode="json"),
        "is_new": result.is_new,
        "dedup_type": result.dedup_type,
    }


@router.get("", response_model=ClaimListResponse)
async def list_claims(
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
        limit=limit,
        offset=offset,
        country=country,
        language=language,
        host=host,
        dossier=dossier,
        date_from=date_from,
        date_to=date_to,
    )
    total = await repo.count_claims(
        country=country,
        language=language,
        host=host,
        dossier=dossier,
        date_from=date_from,
        date_to=date_to,
    )
    items = [ClaimResponse.model_validate(c).model_dump(mode="json") for c in claims]
    return ClaimListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = ClaimRepository(db)
    claim = await repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    return ClaimResponse.model_validate(claim)


@router.patch("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    payload: ClaimUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = ClaimRepository(db)
    claim = await repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    await repo.update_claim(claim)
    return ClaimResponse.model_validate(claim)


@router.get("/{claim_id}/observations", response_model=ObservationListResponse)
async def get_claim_observations(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = ClaimRepository(db)
    claim = await repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    obs_repo = ObservationRepository(db)
    observations = await obs_repo.list_observations_for_claim(claim_id)
    total = await obs_repo.count_observations_for_claim(claim_id)
    items = [ObservationResponse.model_validate(o).model_dump(mode="json") for o in observations]
    return ObservationListResponse(items=items, total=total)


@router.get("/{claim_id}/audit", response_model=AuditEventListResponse)
async def get_claim_audit(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = ClaimRepository(db)
    claim = await repo.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim niet gevonden")
    audit_repo = AuditRepository(db)
    events = await audit_repo.list_audit_events(claim_id=claim_id)
    total = await audit_repo.count_audit_events(claim_id=claim_id)
    items = [AuditEventResponse.model_validate(e).model_dump(mode="json") for e in events]
    return AuditEventListResponse(items=items, total=total)
