# Antigravity Remediation Backlog

This backlog outlines all recommended engineering tasks required to bring the **EU Raw Artifact Discovery Engine** to a fully operational, production-grade state.

---

## Remediation Tasks Matrix

| Task ID | Severity | Component | Summary / Issue Title | Complexity | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **REM-P0-01** | P0 | API Router | Register missing API endpoints in FastAPI app | **S** | None |
| **REM-P0-02** | P0 | Repository / Web | Implement `list_references` & `list_acquisitions` on `ArtifactDiscoveryRepository` | **S** | None |
| **REM-P0-03** | P0 | Entity Service | Fix substring false positive flaw in entity matching | **M** | None |
| **REM-P0-04** | P0 | Connector | Exclude root/index locators from raw artifact discovery | **M** | None |
| **REM-P1-01** | P1 | Acquisition API | Implement download status & blocked acquisition trigger endpoint | **M** | REM-P0-01 |
| **REM-P1-02** | P1 | Repository | Replace in-memory list filtering in `source_stats` with SQL count | **S** | None |
| **REM-P1-03** | P1 | Web / API | Add full-text metadata search and multi-facet filtering | **L** | None |
| **REM-P2-01** | P2 | Test Suite | Install `pytest-cov` and add API integration test suite | **M** | REM-P0-01 |
| **REM-P2-02** | P2 | Frontend UI | Fix table cell word-wrapping and long URL overflow CSS | **S** | None |
| **REM-P2-03** | P2 | Ingest | Implement JSONL / CSV export endpoints for discovered artifacts | **M** | REM-P1-03 |

---

## Detailed Task Backlog

### REM-P0-01: Register Missing API Endpoints
- **Severity**: P0
- **Component**: `app/main.py` / `app/api/`
- **Description**: Add missing routes to `artifacts.py` and register `/api/dashboard/summary` in `app/main.py`.
- **Target Routes**:
  - `GET /api/dashboard/summary`
  - `GET /api/artifacts/{id}`
  - `GET /api/artifacts/{id}/distributions`
  - `GET /api/artifacts/{id}/references`
  - `GET /api/artifacts/{id}/download-status`
  - `POST /api/artifacts/{id}/download`
  - `GET /api/distribution-observations`
  - `GET /api/reference-observations`
- **Complexity**: S

### REM-P0-02: Fix Artifact Detail References & Acquisitions Loading
- **Severity**: P0
- **Component**: `app/repositories/artifact_discoveries.py` & `app/api/web.py`
- **Description**: Implement `list_references(artifact_id)` and `list_acquisitions(artifact_id)` on `ArtifactDiscoveryRepository` so `/artifacts/{id}` accurately renders connected references and acquisitions instead of silently returning empty lists.
- **Complexity**: S

### REM-P0-03: Refactor Entity Matching Substring Check to Word-Boundary Regex
- **Severity**: P0
- **Component**: `app/services/artifact_entity_matching.py`
- **Description**: Replace string inclusion `if name in text:` with regex word boundaries `re.search(r'\b' + re.escape(name) + r'\b', text)` to prevent false country code matches (e.g. matching DE on "Orders", EC on "docx").
- **Complexity**: M

### REM-P0-04: Filter Root & Index Page Locators in Raw Archive Connector
- **Severity**: P0
- **Component**: `app/connectors/raw_archive.py`
- **Description**: Add url filter rules in `extract_candidates` to ignore root domain locators (e.g. `https://cryptome.org/`) and index file paths (e.g. `index.html`).
- **Complexity**: M

### REM-P1-01: Implement Metadata Download Status & Blocked Acquisition Endpoint
- **Severity**: P1
- **Component**: `app/api/artifacts.py` & `app/services/artifact_acquisition.py`
- **Description**: Implement `POST /api/artifacts/{id}/download` to verify `DOWNLOAD_ARTIFACTS` config. When `false`, create an `ArtifactAcquisition` record with `acquisition_status="blocked_by_configuration"` and return HTTP 409 Conflict.
- **Complexity**: M

### REM-P1-02: Optimize Source Stats Database Query
- **Severity**: P1
- **Component**: `app/api/sources.py`
- **Description**: Replace `artifacts = await art_repo.list_discoveries(limit=999)` with direct SQL count `SELECT COUNT(*) FROM artifact_discoveries WHERE source_id = :source_id`.
- **Complexity**: S

### REM-P1-03: Implement Full-Text Search & Multi-Facet Filtering
- **Severity**: P1
- **Component**: `app/repositories/artifact_discoveries.py` & `app/api/web.py`
- **Description**: Add PostgreSQL `ILIKE` or `tsvector` full-text search parameters (`q`, `sha256`, `infohash`, `cid`, `country`, `date_from`, `date_to`) to `/artifacts` and `/api/artifacts`.
- **Complexity**: L

### REM-P2-01: Integration Test Suite & Coverage
- **Severity**: P2
- **Component**: `tests/`
- **Description**: Add `pytest-cov` to `pyproject.toml` and write integration tests for all web & API endpoints.
- **Complexity**: M

### REM-P2-02: CSS Word-Wrap & Responsive Table Layouts
- **Severity**: P2
- **Component**: `app/static/app.css`
- **Description**: Apply `table-layout: fixed` and `word-break: break-all` for locator columns across all tables.
- **Complexity**: S
