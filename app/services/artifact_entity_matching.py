import re
import unicodedata

from app.country_packs.loader import load_country_pack

EU_NAMES = {
    "european commission", "europese commissie", "ec",
    "european parliament", "europees parlement", "ep",
    "council of the european union", "raad van de europese unie",
    "european council", "europese raad",
    "court of justice of the european union", "hof van justitie van de europese unie",
    "european central bank", "europese centrale bank", "ecb",
    "european court of auditors", "europese rekenkamer",
    "european external action service", "eeas",
    "eu council", "eu commission",
    "eu parliament", "europol",
    "eurojust", "frontex",
    "european data protection supervisor", "edps",
    "european investment bank", "eib",
    "european ombudsman",
}

COUNTRY_MAP = {
    "netherlands": "NL", "nederland": "NL", "holland": "NL", "nl": "NL",
    "germany": "DE", "duitsland": "DE", "deutschland": "DE", "de": "DE",
    "france": "FR", "frankrijk": "FR", "fr": "FR",
    "belgium": "BE", "belgie": "BE", "belgium": "BE",
    "austria": "AT", "oostenrijk": "AT",
    "sweden": "SE", "zweden": "SE",
    "denmark": "DK", "denemarken": "DK",
    "finland": "FI", "finland": "FI",
    "ireland": "IE", "ierland": "IE",
    "italy": "IT", "italie": "IT",
    "spain": "ES", "spanje": "ES",
    "portugal": "PT",
    "greece": "GR", "griekenland": "GR",
    "poland": "PL", "polen": "PL",
    "czechia": "CZ", "tsjechie": "CZ",
    "hungary": "HU", "hongarije": "HU",
    "romania": "RO", "roemenie": "RO",
    "bulgaria": "BG", "bulgarije": "BG",
    "croatia": "HR", "kroatie": "HR",
    "slovakia": "SK", "slowakije": "SK",
    "slovenia": "SI", "slovenie": "SI",
    "lithuania": "LT", "litouwen": "LT",
    "latvia": "LV", "letland": "LV",
    "estonia": "EE", "estland": "EE",
    "cyprus": "CY", "cyprus": "CY",
    "malta": "MT",
    "luxembourg": "LU", "luxemburg": "LU",
}


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def match_entities(title: str | None, description: str | None, filename: str | None, locator: str | None, country_code: str) -> tuple[list, list, list]:
    combined = ""
    for part in [title, description, filename, locator]:
        if part:
            combined += _normalize(part) + " "

    countries = list(_find_countries(combined))
    eu_entities = list(_find_eu_entities(combined))
    national_entities = list(_find_national_entities(combined, country_code))
    return countries, eu_entities, national_entities


def _find_countries(text: str) -> set[str]:
    result = set()
    for name, code in COUNTRY_MAP.items():
        if name in text:
            result.add(code)
    return result


def _find_eu_entities(text: str) -> set[str]:
    result = set()
    for name in EU_NAMES:
        if name in text:
            result.add(name.title())
    return result


def _find_national_entities(text: str, country_code: str) -> set[str]:
    result = set()
    try:
        pack = load_country_pack(country_code)
    except Exception:
        return result
    if not pack.entities:
        return result
    for entity in pack.entities.entities:
        names = [entity.canonical_name.lower()] + [a.lower() for a in entity.aliases]
        for n in names:
            if n in text:
                result.add(entity.canonical_name)
                break
    return result
