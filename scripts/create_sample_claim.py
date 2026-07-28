"""Handmatig verificatiescript: registreert één sample claim via de echte
registratieservice. Gebruik dit om te verifiëren dat de volledige keten
werkt: database, service, repositories, audit.
"""
import asyncio
import sys
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.database.session import async_session_factory
from app.services.claim_registration import register_observed_leak_claim


async def main() -> None:
    async with async_session_factory() as session:
        try:
            result = await register_observed_leak_claim(
                session=session,
                title_original="Voorbeeld: mogelijk datalek bij EU-instelling ontdekt",
                first_observed_url="https://example.com/eu-leak-2026",
                source_language="nl",
                summary="Dit is een voorbeeldclaim ter verificatie van de registratieketen.",
                claim_text="Vertrouwelijke documenten over EU-begroting mogelijk gelekt via onbeveiligde server.",
                countries=["NL", "BE"],
                eu_entities=["Europese Commissie"],
                dossiers=["voorbeeld"],
                discovery_method="manual",
                connector_type="manual",
                connector_version="0.1.0",
            )
            await session.commit()
            print(f"Claim geregistreerd: {result.claim.id}")
            print(f"  Nieuw: {result.is_new}")
            print(f"  Dedup type: {result.dedup_type}")
            print(f"  Titel: {result.claim.title_original}")
            print(f"  URL: {result.claim.first_observed_url}")
            print(f"  Host: {result.claim.first_observed_host}")
            print("Registratie geslaagd.")
        except Exception as e:
            await session.rollback()
            print(f"Fout tijdens registratie: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
