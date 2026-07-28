from app.services.url_normalization import normalize_url


def test_lowercase_scheme_and_host():
    result = normalize_url("HTTP://EXAMPLE.COM/Path")
    assert result == "http://example.com/Path"


def test_remove_fragment():
    result = normalize_url("https://example.com/page#section")
    assert "#section" not in result


def test_remove_default_port():
    result = normalize_url("https://example.com:443/page")
    assert result == "https://example.com/page"


def test_keep_non_default_port():
    result = normalize_url("https://example.com:8080/page")
    assert ":8080" in result


def test_sort_query_params():
    result = normalize_url("https://example.com/page?z=1&a=2")
    assert result == "https://example.com/page?a=2&z=1"


def test_remove_tracking_params():
    result = normalize_url("https://example.com/page?utm_source=test&utm_medium=email&a=1")
    assert "utm_source" not in result
    assert "utm_medium" not in result
    assert "a=1" in result


def test_remove_fbclid():
    result = normalize_url("https://example.com/page?fbclid=abc123&keep=yes")
    assert "fbclid" not in result
    assert "keep=yes" in result


def test_remove_gclid():
    result = normalize_url("https://example.com/page?gclid=abc123")
    assert "gclid" not in result


def test_normalize_trailing_slash():
    result = normalize_url("https://example.com/page/")
    assert not result.endswith("/")


def test_root_path_becomes_slash():
    result = normalize_url("https://example.com")
    assert result == "https://example.com/"


def test_empty_path_normalizes():
    result = normalize_url("https://example.com")
    assert result.endswith("/")
