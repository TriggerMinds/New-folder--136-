from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.country_packs.loader import load_all_country_packs, validate_all_country_packs
from app.services.source_sync import sync_country_packs_to_database

router = APIRouter(prefix="/api/country-packs", tags=["country-packs"])


@router.get("")
async def list_country_packs():
    packs = load_all_country_packs()
    return {
        "items": [
            {
                "country_code": p.country_code,
                "status": p.status,
                "languages": [l.model_dump() for l in (p.languages.languages if p.languages else [])],
                "term_count": len(p.leak_terms.terms) if p.leak_terms else 0,
                "entity_count": len(p.entities.entities) if p.entities else 0,
                "source_count": len(p.sources.sources) if p.sources else 0,
                "errors": p.errors,
            }
            for p in packs
        ],
        "total": len(packs),
    }


@router.get("/validation")
async def validate_packs():
    result = validate_all_country_packs()
    return result.model_dump()


@router.post("/sync")
async def sync_packs(db: AsyncSession = Depends(get_db)):
    sync_result = await sync_country_packs_to_database(db)
    await db.commit()
    return {
        "created": sync_result.created,
        "updated": sync_result.updated,
        "disabled": sync_result.disabled,
        "unchanged": sync_result.unchanged,
    }
