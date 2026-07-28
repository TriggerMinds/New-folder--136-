from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.country_packs.loader import load_all_country_packs
from app.database.models.source import Source
from app.repositories.sources import SourceRepository

SYNC_VERSION = "0.1.0"


class SourceSyncResult:
    def __init__(self):
        self.created: int = 0
        self.updated: int = 0
        self.disabled: int = 0
        self.unchanged: int = 0


async def sync_country_packs_to_database(session: AsyncSession) -> SourceSyncResult:
    result = SourceSyncResult()
    repo = SourceRepository(session)
    packs = load_all_country_packs()
    active_packs = [p for p in packs if p.status == "active"]

    existing = await session.execute(select(Source))
    existing_sources = {s.external_id: s for s in existing.scalars().all()}
    synced_external_ids: set[str] = set()

    for pack in active_packs:
        if not pack.sources or not pack.sources.sources:
            continue
        for src_def in pack.sources.sources:
            synced_external_ids.add(src_def.id)
            connector_config = {
                "base_url": src_def.base_url,
                "poll_url": src_def.poll_url,
                "languages": src_def.languages,
            }
            existing_src = existing_sources.get(src_def.id)
            if existing_src:
                needs_update = (
                    existing_src.name != src_def.name
                    or existing_src.country_code != pack.country_code
                    or existing_src.source_type != src_def.type
                    or existing_src.base_url != src_def.base_url
                    or existing_src.poll_url != src_def.poll_url
                    or existing_src.poll_interval_minutes != src_def.poll_interval_minutes
                )
                if needs_update:
                    existing_src.name = src_def.name
                    existing_src.country_code = pack.country_code
                    existing_src.source_type = src_def.type
                    existing_src.base_url = src_def.base_url
                    existing_src.poll_url = src_def.poll_url
                    existing_src.languages = src_def.languages
                    existing_src.poll_interval_minutes = src_def.poll_interval_minutes
                    existing_src.connector_config = connector_config
                    existing_src.country_pack_version = SYNC_VERSION
                    session.add(existing_src)
                    result.updated += 1
                else:
                    result.unchanged += 1
            else:
                src = Source(
                    external_id=src_def.id,
                    name=src_def.name,
                    country_code=pack.country_code,
                    languages=src_def.languages,
                    source_type=src_def.type,
                    base_url=src_def.base_url,
                    poll_url=src_def.poll_url,
                    enabled=src_def.enabled,
                    poll_interval_minutes=src_def.poll_interval_minutes,
                    connector_config=connector_config,
                    country_pack_version=SYNC_VERSION,
                )
                session.add(src)
                result.created += 1

    for ext_id, existing_src in existing_sources.items():
        if ext_id not in synced_external_ids and existing_src.enabled:
            existing_src.enabled = False
            session.add(existing_src)
            result.disabled += 1

    await session.flush()
    return result
