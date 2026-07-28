from app.services.leak_signal_detection import detect_leak_signal


def test_case_insensitive_match():
    result = detect_leak_signal("GELEKT document gevonden", None, ["gelekt"])
    assert result.matched is True
    assert "gelekt" in result.matched_terms


def test_no_match():
    result = detect_leak_signal("Normaal nieuwsbericht", None, ["gelekt", "datalek"])
    assert result.matched is False
    assert len(result.matched_terms) == 0


def test_unicode_normalization():
    result = detect_leak_signal("\uff2c\uff45\uff41\uff4b \u0064\u006f\u0063", None, ["leak doc"])
    assert result.matched is True


def test_compound_term():
    result = detect_leak_signal("Vertrouwelijke documenten uitgelekt bij ministerie", None, ["gelekte documenten"])
    assert result.matched is False


def test_match_in_content():
    result = detect_leak_signal("Normale titel", "Hier staat dat er een datalek heeft plaatsgevonden", ["datalek"])
    assert result.matched is True


def test_empty_terms_no_match():
    result = detect_leak_signal("Gelekt", None, [])
    assert result.matched is False


def test_multiple_terms():
    result = detect_leak_signal("Datalek en hack gemeld", None, ["datalek", "hack"])
    assert result.matched is True
    assert len(result.matched_terms) >= 1


def test_no_title_no_content():
    result = detect_leak_signal(None, None, ["gelekt"])
    assert result.matched is False
