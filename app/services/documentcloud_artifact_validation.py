import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class DocumentCloudValidationResult:
    accepted: bool
    classification: str
    confidence: str
    matched_signals: list[str] = field(default_factory=list)
    rejection_reason: str | None = None
    review_required: bool = False


# Word-boundary patterns for safe matching
_SECRET = re.compile(r"\bsecret\b", re.I)
_CLASSIFIED = re.compile(r"\bclassified\b", re.I)
_CONFIDENTIAL = re.compile(r"\bconfidential\b", re.I)
_INTERNAL = re.compile(r"\binternal\b", re.I)
_RESTRICTED = re.compile(r"\brestricted\b", re.I)
_LEAKED = re.compile(r"\bleaked\b", re.I)
_UNAUTHORIZED = re.compile(r"\bunauthorized\b", re.I)
_SENSITIVE = re.compile(r"\bsensitive\b", re.I)
_NON_PUBLIC = re.compile(r"\bnon.?public\b", re.I)

_LEAK_SIGNALS = [_SECRET, _CLASSIFIED, _CONFIDENTIAL, _INTERNAL, _RESTRICTED, _LEAKED, _UNAUTHORIZED, _SENSITIVE, _NON_PUBLIC]

_INSTITUTION = re.compile(r"\b(commission|parliament|ministry|department|authority|agency|government|council|court|tribunal|committee|directorate)\b", re.I)
_INVESTIGATION = re.compile(r"\binvestigation\b", re.I)
_REGULATORY = re.compile(r"\b(regulation|compliance|procurement|oversight)\b", re.I)
_COURT = re.compile(r"\b(court|trial|lawsuit|indictment|verdict|affidavit|deposition|subpoena)\b", re.I)
_MEMO = re.compile(r"\b(memo|memorandum|correspondence|email|briefing|minutes|note|directive)\b", re.I)
_EXHIBIT = re.compile(r"\bexhibit\b", re.I)
_NEWS = re.compile(r"\b(article|news|press.release|journalist|reporter|newspaper)\b", re.I)
_LEAK = re.compile(r"\bleak\b", re.I)


def _norm(text: str | None) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return unicodedata.normalize("NFKC", text)


def classify_document(title: str | None, description: str | None, organization: str | None, access: str) -> DocumentCloudValidationResult:
    if access != "public":
        return DocumentCloudValidationResult(accepted=False, rejection_reason=f"non-public access: {access}")

    t = _norm(title)
    d = _norm(description)
    o = _norm(organization)
    combined = f"{t} {d} {o}"

    matched_signals = []
    for pat in _LEAK_SIGNALS:
        if pat.search(combined):
            matched_signals.append(pat.pattern.strip("\\b").strip("(?i)").lower().replace("\\b", ""))

    has_exhibit = bool(_EXHIBIT.search(combined))
    has_memo = bool(_MEMO.search(combined))
    has_institution = bool(_INSTITUTION.search(combined))
    has_investigation = bool(_INVESTIGATION.search(combined))
    has_regulatory = bool(_REGULATORY.search(combined))
    has_court = bool(_COURT.search(combined))
    is_news = bool(_NEWS.search(combined))
    has_leak = bool(_LEAK.search(combined))
    has_any_signal = bool(matched_signals)
    has_meaningful = bool(t and (has_institution or has_investigation or has_court or has_regulatory or has_memo))

    # A. Non-public already rejected above

    # B. News/press → reference_only
    if is_news and not (has_any_signal and has_meaningful):
        return DocumentCloudValidationResult(accepted=True, classification="reference_only", confidence="high",
                                            matched_signals=matched_signals)

    # C. Sensitive ambiguity
    if has_any_signal and not has_meaningful and not has_institution:
        return DocumentCloudValidationResult(accepted=True, classification="sensitive_review_required", confidence="low",
                                            matched_signals=matched_signals, review_required=True)

    # D. Strong leak candidate: leak signal + meaningful context
    if has_any_signal and has_meaningful:
        confidence = "high" if (has_leak or has_exhibit) else "medium"
        return DocumentCloudValidationResult(accepted=True, classification="probable_leak_document", confidence=confidence,
                                            matched_signals=matched_signals, review_required=True)

    # E. Court/regulatory/investigation/correspondence/public record
    if has_court and t:
        return DocumentCloudValidationResult(accepted=True, classification="court_record", confidence="high",
                                            matched_signals=matched_signals)
    if has_investigation and t:
        return DocumentCloudValidationResult(accepted=True, classification="investigation_document", confidence="medium",
                                            matched_signals=matched_signals)
    if has_regulatory and t:
        return DocumentCloudValidationResult(accepted=True, classification="regulatory_document", confidence="medium",
                                            matched_signals=matched_signals)
    if has_memo and t:
        return DocumentCloudValidationResult(accepted=True, classification="correspondence", confidence="medium",
                                            matched_signals=matched_signals)

    # F. Public document with organization context
    if t and o:
        return DocumentCloudValidationResult(accepted=True, classification="primary_public_document", confidence="high",
                                            matched_signals=matched_signals)

    # G. Minimal public document
    if t:
        return DocumentCloudValidationResult(accepted=True, classification="primary_public_document", confidence="low",
                                            matched_signals=matched_signals)

    return DocumentCloudValidationResult(accepted=False, classification="irrelevant", rejection_reason="insufficient metadata")
