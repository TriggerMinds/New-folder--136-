"""Valideer alle 27 country packs en rapporteer resultaten."""
import asyncio
import platform
import sys

if platform.system() == "Windows":
    import asyncio as _asyncio
    _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())

from app.country_packs.loader import validate_all_country_packs


def main() -> None:
    result = validate_all_country_packs()
    print(f"Totaal packs: {result.total_packs}")
    print(f"Geldig: {result.valid_packs}")
    print(f"Ongeldig: {result.invalid_packs}")
    if result.errors:
        print("\nFouten:")
        for err in result.errors:
            print(f"  {err.file}: {err.errors}")
    if result.duplicate_source_ids:
        print(f"\nDubbele source IDs: {result.duplicate_source_ids}")
    if result.invalid_packs > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
