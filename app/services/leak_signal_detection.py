import unicodedata


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _match_any(text: str, terms: list[str]) -> list[str]:
    if not terms or not text:
        return []
    lower = text.lower()
    matched: list[str] = []
    for term in terms:
        t_lower = _normalize(term).lower()
        if t_lower in lower:
            matched.append(term)
    return matched


class LeakSignalResult:
    def __init__(self):
        self.matched: bool = False
        self.context_matched_terms: list[str] = []
        self.assertion_matched_terms: list[str] = []
        self.matched_text_locations: list[dict] = []


def detect_leak_signal(
    title: str | None,
    content: str | None,
    context_terms: list[str],
    assertion_terms: list[str],
) -> LeakSignalResult:
    result = LeakSignalResult()
    if not context_terms and not assertion_terms:
        return result

    combined = ""
    if title:
        combined += _normalize(title) + " "
    if content:
        combined += _normalize(content) + " "
    if not combined.strip():
        return result

    result.context_matched_terms = _match_any(combined, context_terms)
    result.assertion_matched_terms = _match_any(combined, assertion_terms)
    result.matched = bool(result.context_matched_terms or result.assertion_matched_terms)

    all_matched = result.context_matched_terms + result.assertion_matched_terms
    lower = combined.lower()
    for i, term in enumerate(all_matched):
        t_lower = _normalize(term).lower()
        idx = lower.find(t_lower)
        if idx != -1:
            result.matched_text_locations.append({"term": term, "index": idx})

    return result


def has_claim_quality(
    result: LeakSignalResult,
    has_origin: bool,
    can_create_primary: bool,
    role: str,
) -> tuple[bool, str]:
    if can_create_primary and role in ("origin_candidate", "distribution", "archive", "mirror"):
        if result.assertion_matched_terms or result.context_matched_terms:
            return True, "primary_role_match"
        return False, "no_match_in_primary_role"

    if result.assertion_matched_terms and has_origin:
        return True, "assertion_plus_origin"
    if result.assertion_matched_terms and not has_origin:
        return False, "assertion_no_origin"
    if result.context_matched_terms and has_origin:
        return False, "context_plus_origin_needs_assertion"
    if result.context_matched_terms and not has_origin:
        return False, "context_only_no_origin"

    return False, "no_match"
