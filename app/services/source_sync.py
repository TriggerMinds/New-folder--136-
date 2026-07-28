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
            connector_config = dict(src_def.connector_config) if src_def.connector_config else {}
            connector_config["base_url"] = src_def.base_url
            connector_config["poll_url"] = src_def.poll_url
            connector_config["languages"] = src_def.languages
            existing_src = existing_sources.get(src_def.id)
            if existing_src:
                cc_str = str(connector_config)
                existing_cc_str = str(existing_src.connector_config)
                src_layer = getattr(src_def, 'source_layer', 'reference_only')
                can_discover = getattr(src_def, 'can_create_artifact_discovery', False)
                can_ref = getattr(src_def, 'can_create_reference_observation', True)
                needs_update = (
                    existing_src.name != src_def.name
                    or existing_src.country_code != pack.country_code
                    or existing_src.source_type != src_def.type
                    or existing_src.source_layer != src_layer
                    or existing_src.source_role != src_def.source_role
                    or existing_src.source_category != src_def.source_category
                    or existing_src.can_create_primary_claim != src_def.can_create_primary_claim
                    or existing_src.can_create_artifact_discovery != can_discover
                    or existing_src.can_create_reference_observation != can_ref
                    or existing_src.discovery_priority != src_def.discovery_priority
                    or existing_src.base_url != src_def.base_url
                    or existing_src.poll_url != src_def.poll_url
                    or existing_src.poll_interval_minutes != src_def.poll_interval_minutes
                    or cc_str != existing_cc_str
                )
                if needs_update:
                    existing_src.name = src_def.name
                    existing_src.country_code = pack.country_code
                    existing_src.source_type = src_def.type
                    existing_src.source_layer = src_layer
                    existing_src.source_role = src_def.source_role
                    existing_src.source_category = src_def.source_category
                    existing_src.can_create_primary_claim = src_def.can_create_primary_claim
                    existing_src.can_create_artifact_discovery = can_discover
                    existing_src.can_create_reference_observation = can_ref
                    existing_src.discovery_priority = src_def.discovery_priority
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
                src_layer = getattr(src_def, 'source_layer', 'reference_only')
                can_discover = getattr(src_def, 'can_create_artifact_discovery', False)
                can_ref = getattr(src_def, 'can_create_reference_observation', True)
                src = Source(
                    external_id=src_def.id,
                    name=src_def.name,
                    country_code=pack.country_code,
                    languages=src_def.languages,
                    source_type=src_def.type,
                    source_layer=src_layer,
                    source_role=src_def.source_role,
                    source_category=src_def.source_category,
                    can_create_primary_claim=src_def.can_create_primary_claim,
                    can_create_artifact_discovery=can_discover,
                    can_create_reference_observation=can_ref,
                    discovery_priority=src_def.discovery_priority,
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
