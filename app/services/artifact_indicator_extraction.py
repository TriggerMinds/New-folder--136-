import re
from urllib.parse import urlparse


class ExtractedArtifacts:
    def __init__(self):
        self.external_urls: list[str] = []
        self.source_self_urls: list[str] = []
        self.repository_urls: list[str] = []
        self.direct_download_urls: list[str] = []
        self.archive_urls: list[str] = []
        self.mirror_urls: list[str] = []
        self.magnet_links: list[str] = []
        self.torrent_hashes: list[str] = []
        self.ipfs_cids: list[str] = []
        self.cryptographic_hashes: list[str] = []
        self.file_names: list[str] = []

    def has_concrete(self) -> bool:
        return bool(
            self.repository_urls
            or self.direct_download_urls
            or self.archive_urls
            or self.mirror_urls
            or self.magnet_links
            or self.torrent_hashes
            or self.ipfs_cids
            or self.cryptographic_hashes
        )


RE_MAGNET = re.compile(r"magnet:\?xt=urn:[a-z0-9]+:[a-f0-9]{32,}(?:&[a-z.]+=[^&\s]+)*", re.IGNORECASE)
RE_TORRENT_HASH = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
RE_IPFS_CIDV0 = re.compile(r"\bQm[1-9A-HJ-NP-Za-km-z]{44}\b")
RE_IPFS_CIDV1 = re.compile(r"\bbafy[2-7a-z]{1,59}\b", re.IGNORECASE)
RE_SHA256 = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
RE_SHA1 = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
RE_MD5 = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
RE_GENERIC_URL = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)

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

ARCHIVE_DOMAINS = [
    "archive.org", "web.archive.org", "archive.today", "archive.is",
    "docdroid.net", "documents.tips", "scribd.com", "academia.edu",
    "docs.google.com", "drive.google.com", "mega.nz", "dropbox.com",
    "1drv.ms", "box.com", "mediafire.com", "sendspace.com",
]

MIRROR_DOMAINS = [
    "ddosecrets.com", "wikileaks.org", "cryptome.org",
    "inteltechniques.com", "raidforums.com", "breached.vc",
]

TRACKING_DOMAIN_PATTERNS = [
    re.compile(r".*\.doubleclick\."),
    re.compile(r".*\.googleadservices\."),
    re.compile(r".*\.facebook\.com/.*(?:tr|pixel)"),
    re.compile(r".*\.googletagmanager\.com"),
    re.compile(r".*\.google-analytics\.com"),
]

STATIC_EXTENSIONS = {".css", ".js", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".woff", ".woff2", ".ttf", ".eot"}

SOCIAL_DOMAINS = {
    "facebook.com", "www.facebook.com", "twitter.com", "x.com",
    "linkedin.com", "instagram.com", "pinterest.com", "reddit.com",
}


def _get_extension(url: str) -> str:
    try:
        path = urlparse(url).path.rstrip("/")
        _, ext = path.rsplit(".", 1)
        return "." + ext.lower()
    except (ValueError, IndexError):
        return ""


def _is_tracking(url: str) -> bool:
    for pat in TRACKING_DOMAIN_PATTERNS:
        if pat.match(url):
            return True
    return False


def _is_static(url: str) -> bool:
    ext = _get_extension(url)
    return ext in STATIC_EXTENSIONS


def _is_social(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host in SOCIAL_DOMAINS or any(host.endswith("." + d) for d in SOCIAL_DOMAINS)


def extract_artifacts(text: str | None, source_poll_url: str | None = None) -> ExtractedArtifacts:
    result = ExtractedArtifacts()
    if not text:
        return result

    result.magnet_links = list(set(RE_MAGNET.findall(text)))
    cid0 = RE_IPFS_CIDV0.findall(text)
    cid1 = RE_IPFS_CIDV1.findall(text)
    result.ipfs_cids = list(set(cid0 + cid1))

    all_hashes_64 = set(RE_SHA256.findall(text))
    all_hashes_40 = set(RE_SHA1.findall(text))
    all_hashes_32 = set(RE_MD5.findall(text))

    already_used: set[str] = set()
    for h in all_hashes_64:
        if h not in already_used:
            result.cryptographic_hashes.append(h)
            already_used.add(h)
    for h in all_hashes_40:
        if h not in already_used:
            already_used.add(h)
            if RE_TORRENT_HASH.fullmatch(h) and len(result.torrent_hashes) < 50:
                result.torrent_hashes.append(h)
            else:
                result.cryptographic_hashes.append(h)
    for h in all_hashes_32:
        if h not in already_used:
            result.cryptographic_hashes.append(h)
            already_used.add(h)

    source_host = urlparse(source_poll_url).hostname if source_poll_url else None
    all_urls = list(set(RE_GENERIC_URL.findall(text)))

    for url in all_urls:
        if _is_tracking(url) or _is_static(url) or _is_social(url):
            continue

        ext = _get_extension(url)
        if ext in ARCHIVE_EXTENSIONS:
            result.direct_download_urls.append(url)
            continue

        if ext in STATIC_EXTENSIONS:
            continue

        is_repo = False
        for pattern in REPO_PATTERNS:
            if pattern.fullmatch(url.strip().rstrip("/").rstrip("#").rstrip("?")):
                result.repository_urls.append(url)
                is_repo = True
                break
        if is_repo:
            continue

        host = urlparse(url).hostname or ""
        if any(ad in host for ad in ARCHIVE_DOMAINS):
            result.archive_urls.append(url)
            continue
        if any(md in host for md in MIRROR_DOMAINS):
            result.mirror_urls.append(url)
            continue

        if source_host and host == source_host:
            result.source_self_urls.append(url)
        else:
            result.external_urls.append(url)

    return result


def extract_file_names(text: str | None) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for ext in ARCHIVE_EXTENSIONS:
        pattern = re.compile(rf'\b([A-Za-z0-9_\-]+{re.escape(ext)})\b', re.IGNORECASE)
        found.extend(pattern.findall(text))
    return list(set(found))


def has_concrete_origin_indicator(artifacts: ExtractedArtifacts, file_names: list[str] | None = None) -> bool:
    if artifacts.has_concrete():
        return True
    return False
