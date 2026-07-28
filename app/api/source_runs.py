from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.source_runs import SourceRunRepository
from app.schemas.source_runs import SourceRunListResponse, SourceRunResponse

router = APIRouter(prefix="/api/source-runs", tags=["source-runs"])


@router.get("", response_model=SourceRunListResponse)
async def list_all_runs(
    source_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = SourceRunRepository(db)
    runs = await repo.list_runs(source_id=source_id, limit=limit, offset=offset)
    total = await repo.count_runs(source_id=source_id)
    items = [SourceRunResponse.model_validate(r).model_dump(mode="json") for r in runs]
    return SourceRunListResponse(items=items, total=total)
