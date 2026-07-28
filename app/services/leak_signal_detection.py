import unicodedata


class LeakSignalResult:
    def __init__(self):
        self.matched: bool = False
        self.matched_terms: list[str] = []
        self.matched_text_locations: list[dict] = []


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def detect_leak_signal(
    title: str | None,
    content: str | None,
    terms: list[str],
) -> LeakSignalResult:
    result = LeakSignalResult()
    if not terms:
        return result

    combined = ""
    if title:
        combined += _normalize(title) + " "
    if content:
        combined += _normalize(content) + " "

    if not combined.strip():
        return result

    combined_lower = combined.lower()

    for term in terms:
        term_lower = _normalize(term).lower()
        idx = combined_lower.find(term_lower)
        if idx != -1:
            result.matched = True
            result.matched_terms.append(term)
            result.matched_text_locations.append({
                "term": term,
                "index": idx,
            })

    return result
