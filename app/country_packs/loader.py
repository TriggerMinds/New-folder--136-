import os
import yaml

from app.config import settings
from app.country_packs.models import (
    CountryPack,
    CountryPackValidationError as ValError,
    CountryPackValidationResult,
    LanguagesFile,
    LeakTermsFile,
    EntitiesFile,
    SourcesFile,
    SourceDef,
)
from app.country_packs.exceptions import CountryPackNotFoundError, CountryPackParseError


EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}


def _load_yaml(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        return data
    except yaml.YAMLError as e:
        raise CountryPackParseError(f"YAML parsefout: {e}", file_path=filepath)
    except FileNotFoundError:
        raise CountryPackNotFoundError(f"Bestand niet gevonden: {filepath}", file_path=filepath)


def _validate_languages_file(filepath: str) -> LanguagesFile | None:
    try:
        data = _load_yaml(filepath)
        if not data or "languages" not in data:
            return None
        return LanguagesFile(**data)
    except CountryPackNotFoundError:
        return None
    except Exception as e:
        raise CountryPackParseError(f"Languages validatiefout: {e}", file_path=filepath)


def _validate_leak_terms_file(filepath: str) -> LeakTermsFile | None:
    try:
        data = _load_yaml(filepath)
        if not data or "terms" not in data:
            code = os.path.basename(os.path.dirname(filepath))
            return LeakTermsFile(country_code=code, status="pending_population", terms=[])
        return LeakTermsFile(**data)
    except CountryPackNotFoundError:
        return None
    except Exception as e:
        raise CountryPackParseError(f"Leak terms validatiefout: {e}", file_path=filepath)


def _validate_entities_file(filepath: str) -> EntitiesFile | None:
    try:
        data = _load_yaml(filepath)
        if not data or "entities" not in data:
            return None
        return EntitiesFile(**data)
    except CountryPackNotFoundError:
        return None
    except Exception as e:
        raise CountryPackParseError(f"Entities validatiefout: {e}", file_path=filepath)


def _validate_sources_file(filepath: str) -> SourcesFile | None:
    try:
        data = _load_yaml(filepath)
        if not data or "sources" not in data:
            return None
        return SourcesFile(**data)
    except CountryPackNotFoundError:
        return None
    except Exception as e:
        raise CountryPackParseError(f"Sources validatiefout: {e}", file_path=filepath)


def load_country_pack(country_code: str) -> CountryPack:
    if country_code not in EU_COUNTRIES:
        raise CountryPackNotFoundError(f"Onbekende EU-landcode: {country_code}")

    pack_dir = os.path.join(settings.country_pack_directory, country_code)
    if not os.path.isdir(pack_dir):
        raise CountryPackNotFoundError(f"Country pack map niet gevonden: {pack_dir}")

    errors: list[str] = []
    langs_file = os.path.join(pack_dir, "languages.yaml")
    terms_file = os.path.join(pack_dir, "leak_terms.yaml")
    entities_file = os.path.join(pack_dir, "entities.yaml")
    sources_file = os.path.join(pack_dir, "sources.yaml")

    languages = None
    try:
        languages = _validate_languages_file(langs_file)
    except Exception as e:
        errors.append(str(e))

    leak_terms = None
    try:
        leak_terms = _validate_leak_terms_file(terms_file)
    except Exception as e:
        errors.append(str(e))

    entities = None
    try:
        entities = _validate_entities_file(entities_file)
    except Exception as e:
        errors.append(str(e))

    sources = None
    try:
        sources = _validate_sources_file(sources_file)
    except Exception as e:
        errors.append(str(e))

    status = "pending_population"
    if languages and languages.status == "active":
        status = "active"
    elif sources and sources.status == "active":
        status = "active"

    return CountryPack(
        country_code=country_code,
        status=status,
        languages=languages,
        leak_terms=leak_terms,
        entities=entities,
        sources=sources,
        errors=errors,
    )


def load_all_country_packs() -> list[CountryPack]:
    packs: list[CountryPack] = []
    for code in EU_COUNTRIES:
        try:
            pack = load_country_pack(code)
            packs.append(pack)
        except CountryPackNotFoundError:
            pass
    return packs


def validate_all_country_packs() -> CountryPackValidationResult:
    result = CountryPackValidationResult()
    all_source_ids: dict[str, str] = {}

    for code in EU_COUNTRIES:
        result.total_packs += 1
        pack_errors: list[str] = []

        try:
            pack = load_country_pack(code)
        except Exception as e:
            result.invalid_packs += 1
            result.errors.append(ValError(file=f"{code}/overall", errors=[str(e)]))
            continue

        if pack.languages and pack.languages.status == "active":
            try:
                LanguagesFile(**pack.languages.model_dump())
            except Exception as e:
                pack_errors.append(f"languages.yaml: {e}")

        if pack.leak_terms and pack.leak_terms.status == "active":
            try:
                LeakTermsFile(**pack.leak_terms.model_dump())
            except Exception as e:
                pack_errors.append(f"leak_terms.yaml: {e}")
            if not pack.leak_terms.terms:
                pack_errors.append("Actief pack vereist minimaal één leak term")

        if pack.entities:
            try:
                EntitiesFile(**pack.entities.model_dump())
            except Exception as e:
                pack_errors.append(f"entities.yaml: {e}")

        if pack.sources:
            try:
                SourcesFile(**pack.sources.model_dump())
            except Exception as e:
                pack_errors.append(f"sources.yaml: {e}")
            if pack.sources.sources:
                for s in pack.sources.sources:
                    if s.id in all_source_ids:
                        result.duplicate_source_ids.append(s.id)
                    all_source_ids[s.id] = code

        if pack.errors:
            pack_errors.extend(pack.errors)

        if pack_errors:
            result.invalid_packs += 1
            for err in pack_errors:
                result.errors.append(ValError(file=f"{code}", errors=[err]))
        else:
            result.valid_packs += 1

    return result
