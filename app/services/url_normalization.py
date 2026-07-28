from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid",
}

STANDARD_PORTS: dict[str, int] = {
    "http": 80,
    "https": 443,
}


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    port = parsed.port
    path = parsed.path.rstrip("/") if parsed.path else ""
    query = parsed.query
    fragment = ""

    if port is not None and STANDARD_PORTS.get(scheme) == port:
        port = None

    if path == "":
        path = "/"

    params = parse_qs(query, keep_blank_values=True)
    cleaned = {}
    for key in sorted(params.keys()):
        if key.lower() not in TRACKING_PARAMS:
            cleaned[key] = params[key]

    new_query = urlencode(cleaned, doseq=True) if cleaned else ""

    netloc = hostname
    if port is not None:
        netloc = f"{hostname}:{port}"

    return urlunparse((scheme, netloc, path, parsed.params, new_query, fragment))
