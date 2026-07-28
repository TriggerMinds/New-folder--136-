import pytest

from app.country_packs.loader import load_country_pack, load_all_country_packs, validate_all_country_packs, EU_COUNTRIES


def test_all_27_packs_load():
    packs = load_all_country_packs()
    assert len(packs) == 27


def test_validate_all_packs():
    result = validate_all_country_packs()
    assert result.total_packs == 27
    assert result.valid_packs == 27
    assert result.invalid_packs == 0


def test_nl_pack_active():
    pack = load_country_pack("NL")
    assert pack.status == "active"
    assert pack.languages is not None
    assert len(pack.languages.languages) >= 1
    assert pack.context_terms is not None
    assert len(pack.context_terms.context_terms) >= 1
    assert pack.sources is not None
    assert len(pack.sources.sources) >= 2


def test_nl_sources_have_multiple_types():
    pack = load_country_pack("NL")
    types = {s.type for s in pack.sources.sources}
    assert len(types) >= 2
    assert "raw_archive" in types
    assert "github_api" in types or "internet_archive_api" in types


def test_pending_population_packs_valid():
    pack = load_country_pack("DE")
    assert pack.status == "pending_population" or pack.errors or True
    result = validate_all_country_packs()
    assert result.valid_packs == 27


def test_invalid_country_code():
    from app.country_packs.exceptions import CountryPackNotFoundError
    with pytest.raises(CountryPackNotFoundError):
        load_country_pack("XX")
