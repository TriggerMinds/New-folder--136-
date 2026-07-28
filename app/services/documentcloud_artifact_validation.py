from dataclasses import dataclass


@dataclass
class DocumentCloudValidationResult:
    accepted: bool = False
    classification: str = "irrelevant"
    confidence: str = "low"
    matched_signals: list[str] = None
    rejection_reason: str = ""
    review_required: bool = False


LEAK_SIGNALS = [
    "confidential", "internal", "non-public", "restricted", "classified",
    "leaked", "leak", "unauthorized", "sensitive", "secret",
]

INSTITUTION_SIGNALS = [
    "commission", "parliament", "ministry", "department", "authority",
    "agency", "government", "council", "court", "tribunal",
]

DOCUMENT_TYPES = [
    "memo", "memorandum", "email", "correspondence", "exhibit",
    "report", "investigation", "briefing", "note", "minutes",
]


def classify_document(title: str, description: str, organization: str, access: str) -> DocumentCloudValidationResult:
    if access != "public":
        return DocumentCloudValidationResult(accepted=False, rejection_reason=f"non-public access: {access}")

    combined = (title or "") + " " + (description or "") + " " + (organization or "")
    combined_lower = combined.lower()

    matched_signals = []
    for signal in LEAK_SIGNALS:
        if signal in combined_lower:
            matched_signals.append(signal)

    inst_matches = [s for s in INSTITUTION_SIGNALS if s in combined_lower]
    doc_matches = [s for s in DOCUMENT_TYPES if s in combined_lower]

    is_public_doc = bool(organization and title)
    is_investigation = "investigation" in combined_lower or "exhibit" in combined_lower
    is_regulatory = "regulation" in combined_lower or "compliance" in combined_lower or "procurement" in combined_lower
    is_court = "court" in combined_lower or "trial" in combined_lower or "lawsuit" in combined_lower
    is_memo = "memo" in combined_lower or "correspondence" in combined_lower or "email" in combined_lower
    is_internal = any(s in combined_lower for s in ["internal", "confidential", "classified", "restricted"])
    is_news = "article" in combined_lower or "news" in combined_lower or "press release" in combined_lower

    result = DocumentCloudValidationResult(accepted=True)

    if is_internal and doc_matches and (inst_matches or is_investigation):
        result.classification = "probable_leak_document"
        result.confidence = "high" if (len(matched_signals) >= 2 and inst_matches) else "medium"
        result.matched_signals = matched_signals + doc_matches + inst_matches
        result.review_required = True
        return result

    if is_court and title and organization:
        result.classification = "court_record"
        result.confidence = "high"
        result.matched_signals = matched_signals
        return result

    if is_investigation and title:
        result.classification = "investigation_document"
        result.confidence = "medium"
        result.matched_signals = matched_signals
        return result

    if is_regulatory and title:
        result.classification = "regulatory_document"
        result.confidence = "medium"
        result.matched_signals = matched_signals
        return result

    if is_memo and title:
        result.classification = "correspondence"
        result.confidence = "medium"
        result.matched_signals = matched_signals
        return result

    if is_public_doc:
        result.classification = "primary_public_document"
        result.confidence = "high"
        result.matched_signals = matched_signals
        return result

    if is_news:
        result.classification = "reference_only"
        result.confidence = "low"
        result.matched_signals = matched_signals
        return result

    result.classification = "irrelevant"
    result.confidence = "low"
    result.accepted = False
    result.rejection_reason = "matched no relevant classification signals"
    return result
