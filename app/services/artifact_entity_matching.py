import re
import unicodedata
from urllib.parse import urlparse

from app.country_packs.loader import load_country_pack

EU_ENTITIES = [
    ("european commission", "European Commission"),
    ("europese commissie", "European Commission"),
    ("european parliament", "European Parliament"),
    ("europees parlement", "European Parliament"),
    ("european council", "European Council"),
    ("europese raad", "European Council"),
    ("european central bank", "European Central Bank"),
    ("europese centrale bank", "European Central Bank"),
    ("court of justice of the european union", "Court of Justice of the European Union"),
    ("european court of auditors", "European Court of Auditors"),
    ("europol", "Europol"),
    ("eurojust", "Eurojust"),
    ("frontex", "Frontex"),
    ("european external action service", "European External Action Service"),
]

COUNTRY_MAP = [
    (re.compile(r"\bnetherlands\b", re.I), "NL"),
    (re.compile(r"\bnederland\b", re.I), "NL"),
    (re.compile(r"\bgermany\b", re.I), "DE"),
    (re.compile(r"\bduitsland\b", re.I), "DE"),
    (re.compile(r"\bdeutschland\b", re.I), "DE"),
    (re.compile(r"\bfrance\b", re.I), "FR"),
    (re.compile(r"\bfrankrijk\b", re.I), "FR"),
    (re.compile(r"\bbelgium\b", re.I), "BE"),
    (re.compile(r"\bbelgie\b", re.I), "BE"),
    (re.compile(r"\baustria\b", re.I), "AT"),
    (re.compile(r"\boostenrijk\b", re.I), "AT"),
    (re.compile(r"\bsweden\b", re.I), "SE"),
    (re.compile(r"\bzweden\b", re.I), "SE"),
    (re.compile(r"\bdenmark\b", re.I), "DK"),
    (re.compile(r"\bdenemarken\b", re.I), "DK"),
    (re.compile(r"\bfinland\b", re.I), "FI"),
    (re.compile(r"\bfinland\b", re.I), "FI"),
    (re.compile(r"\bireland\b", re.I), "IE"),
    (re.compile(r"\bierland\b", re.I), "IE"),
    (re.compile(r"\bitaly\b", re.I), "IT"),
    (re.compile(r"\bitalie\b", re.I), "IT"),
    (re.compile(r"\bspain\b", re.I), "ES"),
    (re.compile(r"\bspanje\b", re.I), "ES"),
    (re.compile(r"\bportugal\b", re.I), "PT"),
    (re.compile(r"\bgreece\b", re.I), "GR"),
    (re.compile(r"\bgriekenland\b", re.I), "GR"),
    (re.compile(r"\bpoland\b", re.I), "PL"),
    (re.compile(r"\bpolen\b", re.I), "PL"),
    (re.compile(r"\bhungary\b", re.I), "HU"),
    (re.compile(r"\bhongarije\b", re.I), "HU"),
    (re.compile(r"\bromania\b", re.I), "RO"),
    (re.compile(r"\broemenie\b", re.I), "RO"),
    (re.compile(r"\bbulgaria\b", re.I), "BG"),
    (re.compile(r"\bbulgarije\b", re.I), "BG"),
]

HOST_COUNTRY = {
    ".nl": "NL", ".de": "DE", ".fr": "FR", ".be": "BE", ".at": "AT",
    ".se": "SE", ".dk": "DK", ".fi": "FI", ".ie": "IE", ".it": "IT",
    ".es": "ES", ".pt": "PT", ".gr": "GR", ".pl": "PL", ".hu": "HU",
    ".ro": "RO", ".bg": "BG", ".cz": "CZ", ".sk": "SK", ".si": "SI",
    ".hr": "HR", ".lt": "LT", ".lv": "LV", ".ee": "EE", ".cy": "CY",
    ".mt": "MT", ".lu": "LU",
}


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _country_from_hostname(locator: str | None) -> list[str]:
    if not locator:
        return []
    hostname = urlparse(locator).hostname
    if not hostname:
        return []
    hostname = hostname.lower()
    for suffix, code in HOST_COUNTRY.items():
        if hostname == suffix or hostname.endswith(suffix):
            return [code]
    return []


def match_entities(title: str | None, description: str | None, filename: str | None, locator: str | None, country_code: str) -> tuple[list, list, list]:
    combined = ""
    for part in [title, description, filename]:
        if part:
            combined += _norm(part) + " "

    countries = set()
    for pattern, code in COUNTRY_MAP:
        if pattern.search(combined):
            countries.add(code)
    countries.update(_country_from_hostname(locator))

    eu_entities = set()
    for search_name, canonical_name in EU_ENTITIES:
        pat = re.compile(r"\b" + re.escape(search_name) + r"\b", re.I)
        if pat.search(combined):
            eu_entities.add(canonical_name)

    national_entities = set()
    try:
        pack = load_country_pack(country_code)
    except Exception:
        pack = None
    if pack and pack.entities:
        for entity in pack.entities.entities:
            names = [entity.canonical_name.lower()] + [a.lower() for a in entity.aliases]
            for n in names:
                pat = re.compile(r"\b" + re.escape(_norm(n)) + r"\b", re.I)
                if pat.search(combined):
                    national_entities.add(entity.canonical_name)
                    break

    return sorted(countries), sorted(eu_entities), sorted(national_entities)
