# Antigravity Database Audit Findings

## Executive Summary Database Integrity

An in-depth read-only SQL audit was conducted on the PostgreSQL database (`eu_leak`). The database schema consists of 7 Alembic migrations up to head `0007`.

Overall, data integrity for existing Cryptome discoveries is high with **0 duplicate hashes**, **0 duplicate canonical locators**, and **0 orphaned distribution observations**. However, structural issues and data contamination patterns were identified.

---

## 1. Table Row Counts & Source Classifications

| Entity Table | Record Count | Classification / Status Details |
| :--- | :--- | :--- |
| **`sources`** | **22** | 1 Active, 8 Inactive, 13 Historical |
| — Active `primary_raw` | **1** | Cryptome Document Archive |
| — Active `reference_only` | **0** | (5 configured in country packs, but present as active=0 in current DB state) |
| **`source_runs`** | **114** | Executed ingestion runs |
| **`artifact_discoveries`** | **408** | Unique raw artifact discoveries |
| **`distribution_observations`** | **408** | Unique distribution records linked 1-to-1 with discoveries |
| **`reference_observations`** | **0** | No reference observations registered |
| **`artifact_acquisitions`** | **0** | No acquisition audit records logged |
| **`observed_leak_claims`** | **2** | Legacy claim records |
| **`source_signals`** | **2** | Signal records |

---

## 2. Deduplication & Unique Constraints Verification

| Column / Constraint | Duplicate Count | Status | Notes |
| :--- | :--- | :--- | :--- |
| `sha256` | **0** | PASSED | All non-null SHA-256 hashes are unique. |
| `torrent_infohash` | **0** | PASSED | Unique across all discoveries. |
| `ipfs_cid` | **0** | PASSED | Unique across all discoveries. |
| `archive_identifier` | **0** | PASSED | Unique across all discoveries. |
| `canonical_locator` | **0** | PASSED | Unique across all discoveries. |
| `repository_url` + `repository_ref` | **0** | PASSED | Unique across all discoveries. |
| Distribution Unique Key (`artifact_discovery_id` + `source_id` + `canonical_locator`) | **0** | PASSED | Unique constraint enforced on migration `0007`. |

---

## 3. Referential Integrity & Orphan Records

| Integrity Check | Orphan Count | Severity | Risk & Impact |
| :--- | :--- | :--- | :--- |
| **Artifacts without Distribution** | **0** | PASSED | Every artifact has at least 1 distribution observation. |
| **Distributions without Artifact** | **0** | PASSED | No orphaned distribution observations. |
| **Acquisitions without Artifact** | **0** | PASSED | No orphaned acquisition records. |
| **References without Artifact/Claim** | **0** | PASSED | No orphaned reference observations. |
| **Artifacts from Reference-Only Sources** | **0** | PASSED | Reference-only sources have not generated artifact discoveries. |
| **Artifacts from Historical Sources** | **0** | PASSED | Historical sources have not generated artifact discoveries. |
| **Active Sources Disabled** | **0** | PASSED | `enabled=true` aligns with `lifecycle_status='active'`. |
| **Inactive Sources Enabled** | **0** | PASSED | No inactive sources have `enabled=true`. |
| **Historical Sources Enabled** | **0** | PASSED | Historical sources have `enabled=false`. |
| **Empty Canonical Locators** | **0** | PASSED | All artifacts have non-empty `canonical_locator`. |
| **Homepage/Navigation Locators** | **11** | **P0** | **11 raw artifacts have root URLs or index page URLs registered as raw artifacts** (e.g., `https://cryptome.org/` or `https://cryptome.org/index.html`). |
| **Unrealistic Content Length** | **0** | PASSED | All size values are valid or null. |
| **Invalid `source_run_id`** | **0** | PASSED | All `source_run_id` references point to existing `source_runs`. |

---

## 4. Specific Database Integrity Findings

### DB-FINDING-01: Root Page Locator Contamination (11 Artifacts)
- **Severity**: P0
- **Evidence**: 11 records in `artifact_discoveries` have canonical locators pointing to index pages (e.g. `https://cryptome.org/`, `https://cryptome.org/index.html`, `https://cryptome.org/2025/index.html`).
- **Cause**: Raw archive connector parses links from index HTML without excluding self-referential index/navigation links.
- **Impact**: Index pages are misclassified as raw document artifacts.

### DB-FINDING-02: Missing Foreign Key CASCADE / Indexes on References & Acquisitions
- **Severity**: P1
- **Evidence**: `reference_observations` table lacks foreign key constraints to `artifact_discoveries` and `observed_leak_claims`.
- **Cause**: Database schema migrations (`0005`) defined `artifact_discovery_id` as a plain UUID column without an explicit SQLAlchemy `ForeignKey` constraint.
- **Impact**: Potential orphan records if discoveries are deleted.
