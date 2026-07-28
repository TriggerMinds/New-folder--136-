from uuid import UUID

from sqlalchemy import case, func, select, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.source import Source


def _lifecycle_order() -> object:
    return case(
        (Source.lifecycle_status == "active", 1),
        (Source.lifecycle_status == "inactive", 2),
        (Source.lifecycle_status == "broken", 3),
        (Source.lifecycle_status == "blocked", 4),
        (Source.lifecycle_status == "historical", 5),
        (Source.lifecycle_status == "superseded", 6),
        else_=99,
    )


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source(self, source: Source) -> Source:
        self.session.add(source)
        await self.session.flush()
        return source

    async def get_source(self, source_id: UUID) -> Source | None:
        stmt = select(Source).where(Source.id == source_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sources(
        self, limit: int = 100, offset: int = 0, enabled_only: bool = False,
        lifecycle_status: str | None = None, source_layer: str | None = None,
        present_in_country_pack: bool | None = None, country_code: str | None = None,
        include_historical: bool = False,
    ) -> list[Source]:
        stmt = select(Source)
        if enabled_only:
            stmt = stmt.where(Source.enabled.is_(True))
        if lifecycle_status:
            stmt = stmt.where(Source.lifecycle_status == lifecycle_status)
        if source_layer:
            stmt = stmt.where(Source.source_layer == source_layer)
        if present_in_country_pack is not None:
            stmt = stmt.where(Source.present_in_country_pack == present_in_country_pack)
        if country_code:
            stmt = stmt.where(Source.country_code == country_code)
        if not include_historical:
            stmt = stmt.where(Source.lifecycle_status != "historical")
        stmt = stmt.order_by(_lifecycle_order(), Source.source_layer, Source.name).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_sources(self, enabled_only: bool = False) -> int:
        stmt = select(func.count(Source.id))
        if enabled_only:
            stmt = stmt.where(Source.enabled.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_summary(self) -> dict:
        total = await self.session.execute(select(func.count(Source.id)))
        active = await self.session.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "active"))
        inactive = await self.session.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "inactive"))
        broken = await self.session.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "broken"))
        blocked = await self.session.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "blocked"))
        historical = await self.session.execute(select(func.count(Source.id)).where(Source.lifecycle_status == "historical"))
        primary_raw = await self.session.execute(select(func.count(Source.id)).where(Source.source_layer == "primary_raw", Source.lifecycle_status == "active"))
        ref_only = await self.session.execute(select(func.count(Source.id)).where(Source.source_layer == "reference_only", Source.present_in_country_pack == True))
        return {
            "total_current": total.scalar() or 0,
            "active": active.scalar() or 0,
            "inactive": inactive.scalar() or 0,
            "broken": broken.scalar() or 0,
            "blocked": blocked.scalar() or 0,
            "historical": historical.scalar() or 0,
            "primary_raw_active": primary_raw.scalar() or 0,
            "reference_only_active": ref_only.scalar() or 0,
        }

    async def update_source_status(
        self, source: Source, *, last_checked_at: object | None = None,
        last_success_at: object | None = None, last_error_at: object | None = None,
        last_error: str | None = None, consecutive_failures: int | None = None,
    ) -> Source:
        if last_checked_at is not None:
            source.last_checked_at = last_checked_at
        if last_success_at is not None:
            source.last_success_at = last_success_at
        if last_error_at is not None:
            source.last_error_at = last_error_at
        if last_error is not None:
            source.last_error = last_error
        if consecutive_failures is not None:
            source.consecutive_failures = consecutive_failures
        self.session.add(source)
        await self.session.flush()
        return source
