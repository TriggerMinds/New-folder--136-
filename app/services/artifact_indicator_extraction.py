import re
from urllib.parse import urlparse


class ExtractedArtifacts:
    def __init__(self):
        self.urls: list[str] = []
        self.repository_urls: list[str] = []
        self.download_urls: list[str] = []
        self.magnet_links: list[str] = []
        self.torrent_hashes: list[str] = []
        self.ipfs_cids: list[str] = []
        self.sha256_hashes: list[str] = []
        self.sha1_hashes: list[str] = []
        self.md5_hashes: list[str] = []
        self.file_names: list[str] = []


RE_MAGNET = re.compile(r"magnet:\?xt=urn:[a-z0-9]+:[a-f0-9]{32,}(?:&[a-z.]+=[^&\s]+)*", re.IGNORECASE)
RE_TORRENT_HASH = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
RE_IPFS_CIDV0 = re.compile(r"\bQm[1-9A-HJ-NP-Za-km-z]{44}\b")
RE_IPFS_CIDV1 = re.compile(r"\bbafy[2-7a-z]{1,59}\b", re.IGNORECASE)
RE_SHA256 = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
RE_SHA1 = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
RE_MD5 = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
RE_GENERIC_URL = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

ARCHIVE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".json", ".xml",
    ".zip", ".7z", ".tar", ".gz", ".tgz", ".rar", ".eml", ".mbox",
    ".sql", ".dump", ".sqlite", ".db", ".pst", ".ost",
}

REPO_PATTERNS = [
    re.compile(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\b|/|#|\?|$)", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?gitlab\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\b|/|#|\?|$)", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?bitbucket\.org/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\b|/|#|\?|$)", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?codeberg\.org/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\b|/|#|\?|$)", re.IGNORECASE),
    re.compile(r"https?://(?:www\.)?gitlab\.[a-z]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\b|/|#|\?|$)", re.IGNORECASE),
]


def extract_artifacts(text: str | None) -> ExtractedArtifacts:
    result = ExtractedArtifacts()
    if not text:
        return result

    result.magnet_links = list(set(RE_MAGNET.findall(text)))
    cid0 = RE_IPFS_CIDV0.findall(text)
    cid1 = RE_IPFS_CIDV1.findall(text)
    result.ipfs_cids = list(set(cid0 + cid1))

    all_hashes_40 = set(RE_SHA1.findall(text))
    all_hashes_32 = set(RE_MD5.findall(text))
    all_hashes_64 = set(RE_SHA256.findall(text))

    already_used: set[str] = set()
    for h in all_hashes_64:
        if h not in already_used:
            result.sha256_hashes.append(h)
            already_used.add(h)
    for h in all_hashes_40:
        if h not in already_used:
            already_used.add(h)
            is_torrent = bool(RE_TORRENT_HASH.fullmatch(h))
            if is_torrent and len(result.torrent_hashes) < 50:
                result.torrent_hashes.append(h)
            else:
                result.sha1_hashes.append(h)
    for h in all_hashes_32:
        if h not in already_used:
            result.md5_hashes.append(h)
            already_used.add(h)

    all_urls = list(set(RE_GENERIC_URL.findall(text)))
    for url in all_urls:
        for pattern in REPO_PATTERNS:
            if pattern.fullmatch(url.strip().rstrip("/").rstrip("#").rstrip("?")):
                result.repository_urls.append(url)
                break
        else:
            ext = _get_extension(url)
            if ext in ARCHIVE_EXTENSIONS:
                result.download_urls.append(url)
            else:
                result.urls.append(url)

    return result


def _get_extension(url: str) -> str:
    try:
        path = urlparse(url).path.rstrip("/")
        _, ext = path.rsplit(".", 1)
        return "." + ext.lower()
    except (ValueError, IndexError):
        return ""


def extract_file_names(text: str | None) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for ext in ARCHIVE_EXTENSIONS:
        pattern = re.compile(rf'\b([A-Za-z0-9_\-]+{re.escape(ext)})\b', re.IGNORECASE)
        found.extend(pattern.findall(text))
    return list(set(found))
