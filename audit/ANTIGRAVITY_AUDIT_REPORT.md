# ONAFHANKELIJK PRODUCTIE-AUDITRAPPORT
## EU RAW ARTIFACT DISCOVERY ENGINE

---

> [!IMPORTANT]
> **Audit Status**: VOLTOOID  
> **Audittijdstip**: 2026-07-28  
> **Locatie Codebase**: `C:\Users\gewoo\New folder (136)`  
> **Repository Commit**: `178d6f20489eb9fdeb0ac2e710cad612c17d2d53` (HEAD -> `main`)  
> **Hard Rule Naleving**: Er zijn **geen applicatiecode**, **geen tests**, en **geen databasegegevens** gewijzigd of verwijderd gedurende deze audit.

---

## 1. Executive Summary

Een onafhankelijke, integrale audit is uitgevoerd op de lokaal draaiende **EU Raw Artifact Discovery Engine**. De audit beoordeelde de architectuur, runtime routes, database-integriteit, connector-acceptatie (Cryptome), bron-lifecycle, metadata-first regels, testsuite en professionele geschiktheid voor raw-document- en leak-onderzoekers.

### Kernbevindingen Overzicht
- **Totaal P0 (Kritiek)**: **4** (Ontbrekende/ongeregistreerde API-routes, `hasattr`-bypasses van referenties op detailpagina, ernstige substring-fout in entity matching, homepage-locatorbesmetting).
- **Totaal P1 (Hoog)**: **3** (Ontbrekende download status/audit-endpoints, N+1 in-memory aftapping in source stats, ontbreken van full-text/hash/dossier-zoekfunctionaliteit).
- **Totaal P2 (Medium)**: **3** (Geen pytest-cov, ontbrekende API-integratietests, UI tabel-overflow op lange locators).
- **Totaal P3 (Laag)**: **2** (Paginering ontbreekt op `/distributions` en `/references`, datumformatter UX).

---

## 2. Exacte Repository- en Omgevingsstatus

### Omgevingsparameters
- **Werkdirectory**: `C:\Users\gewoo\New folder (136)`
- **Git Branch**: `main`
- **HEAD Commit**: `178d6f2` (*Phase 3I-B: distribution/reference/detail pages, source-run filtering, datetime formatter, dashboard metrics, entity matching, navigation update*)
- **Git Tree**: Clean (geen ongecommitteerde wijzigingen in applicatiecode)
- **Python Omgeving**: Python 3.12.10 in virtuele omgeving `.venv`
- **Database Status**: PostgreSQL 16 (`docker-compose` container `newfolder136-postgres-1`, status healthy)
- **Alembic Versie**: `0007` (head: `0007_artifact_dedup_and_distribution_uniq.py`)
- **Migratiedivergentie**: **Geen** (alembic current = alembic head = `0007`)
- **Actieve Config**: `DOWNLOAD_ARTIFACTS=false`, `APP_HOST=127.0.0.1`, `APP_PORT=8000`

---

## 3. Bevestigd Werkende Functies (`working`)

1. **Raw Artifact Feed (`/` & `/artifacts`)**:
   - Renders 408 ontdekte Cryptome-artifacts in een chronologische raw feed met pagination parameters.
2. **Cryptome Ingestie & Deduplicatie**:
   - De connector verwerkt 408 Cryptome-items. Een 2e executie op een ongewijzigde index genereert **exact 0 nieuwe artifacts** en **0 nieuwe distributions** (idempotent).
3. **Database Unieke Constraints (`0007`)**:
   - `sha256`, `torrent_infohash`, `ipfs_cid`, `archive_identifier`, `canonical_locator` en distribution unique key (`artifact_discovery_id`, `source_id`, `canonical_locator`) bevatten **0 duplicaten**.
4. **Bron Lifecycle Beheer (`/sources`)**:
   - Onderscheidt `active` (1: Cryptome), `inactive` (8), en `historical` (13). Directe `POST /api/sources/{id}/run` op een disabled/inactive bron blokkeert correct met **HTTP 409 Conflict**.
5. **System Health Endpoint (`/health` & `/system/health`)**:
   - Geeft HTTP 200 OK en retourneert JSON status `healthy` met actieve database-verbinding.
6. **Country Packs Loader (`/country-packs`)**:
   - Laadt alle 27 EU-lidstaat configuraties correct in en toont de bronstatistieken per land.

---

## 4. Gedeeltelijk Werkende Functies (`partially_working`)

1. **Artifact Detailpagina (`/artifacts/{id}`)**:
   - Renders basismetadata van het artifact, maar toont **altijd 0 referenties** en **0 acquisities** doordat de web-route met `hasattr` ontbrekende repository-methoden omzeilt.
2. **Legacy Claims Interface (`/claims`)**:
   - Bestaat in code en UI uit eerdere fasen, maar is losgekoppeld van het nieuwe `ArtifactDiscovery`-systeem.
3. **Source Stats API (`/api/sources/{id}/stats`)**:
   - Functioneert voor kleine aantallen, maar gebruikt `list_discoveries(limit=999)` in geheugen in plaats van een SQL COUNT query.

---

## 5. Gebroken Functies (`broken`)

1. **Entity Matching Script & Service (`app/services/artifact_entity_matching.py`)**:
   - Gebruikt een naïeve substring match (`if name in text:`) op 2-letterige landcodes. Resultaat: de tekst `"Orders"` matcht landcode `DE`, en de extensie `.docx` matcht EU-entiteit `EC`.
2. **Artifact Detail Navigation & Sub-resources**:
   - UI detailpagina's kunnen geen sub-resources (distributies/referenties) ophalen via API-call omdat API-routes ontbreken.

---

## 6. Ontbrekende Functies (`missing`)

1. **API Dashboard Summary (`GET /api/dashboard/summary`)**:
   - Service-functie `get_dashboard_summary()` bestaat wel in `app/services/dashboard.py`, maar de FastAPI API-route is nergens geregistreerd (**HTTP 404**).
2. **API Artifact Detail & Child Routes**:
   - `GET /api/artifacts/{id}`, `GET /api/artifacts/{id}/distributions`, `GET /api/artifacts/{id}/references` ontbreken in `app/api/artifacts.py` (**HTTP 404**).
3. **Download Trigger & Acquisition Audit Log**:
   - `POST /api/artifacts/{id}/download`, `POST /artifacts/{id}/download`, `GET /api/artifacts/{id}/download-status` ontbreken (**HTTP 404**). Er is geen mogelijkheid voor een gebruiker om een metadata-only acquisitiepoging vast te leggen.
4. **API Distribution & Reference Observations**:
   - `GET /api/distribution-observations` en `GET /api/reference-observations` ontbreken (**HTTP 404**).
5. **Full-Text Metadata Search & Multi-Facet Filtering**:
   - Geen zoekbalk voor titel/filename/hash/dossier/land op `/artifacts` of `/api/artifacts`.

---

## 7. Misleidende UI-, API- en Database-Uitkomsten (`misleading`)

1. **`hasattr` Silence in Detailpagina (`app/api/web.py`)**:
   - Code controleert `if hasattr(repo, "list_references"):` en `if hasattr(repo, "list_acquisitions"):`. Omdat deze methoden op `ArtifactDiscoveryRepository` ontbreken, evalueert dit geruisloos als `False`. De UI toont "(0)" zonder enige foutmelding of log.
2. **Homepage Locators als Raw Artifacts**:
   - 11 `ArtifactDiscovery` records in de database hebben als `canonical_locator` een indexpagina (bijv. `https://cryptome.org/` of `https://cryptome.org/index.html`).

---

## 8. Database-Integriteitsbevindingen

| Metric | Resultaat | Status |
| :--- | :--- | :--- |
| Database Tabellen | 11 tabellen | OK |
| Migration Head | 0007 | OK |
| Directe Duplicaten (SHA256/CID/Infohash) | 0 | OK |
| Distribution Unique Constraints | 0 duplicaten | OK |
| Orphan Distributions / Acquisitions | 0 | OK |
| Navigatie/Index Locators in Artifacts | **11 records** | **P0 Finding** |

---

## 9. Testkwaliteitsbevindingen

- **Verzamelde Tests**: 50 tests in `tests/`.
- **Slagingspercentage**: 100% (50 passed).
- **Test Coverage**: `pytest-cov` is **niet geïnstalleerd**.
- **Testkwaliteit-beoordeling**:
  - Alle 50 tests zijn unit tests op pure functies of in-memory mocks.
  - **Nul integration tests** voor FastAPI web-routes of API-endpoints.
  - De testsuite sloeg aan als groen ondanks het ontbreken van 9 API-routes en de ernstige entity-matching bug.

---

## 10. Securitybevindingen

1. **OpenAPI / Swagger Public Accessibility**:
   - `/docs` en `/openapi.json` zijn openbaar toegankelijk zonder authenticatie. Indien lokaal gebonden aan `127.0.0.1` is dit acceptabel, maar vereist authenticatie/IP-restricte bij netwerkblootstelling.
2. **Input Sanitization & Path Traversal Guard**:
   - Downloadpad-afhandeling in downloadservices (statisch geïnspecteerd) vereist strikte `Path.resolve()` check om path traversal te voorkomen zodra downloads enabled worden.
3. **External URL Handling**:
   - Ingestie opent externe HTTP-bronnen. Maximaal aantal redirects en timeouts (10s) zijn correct geconfigureerd in connectors.

---

## 11. Professionele Productgap-Analyse

Evaluatie vanuit het perspectief van een professionele raw-document/leak-onderzoeker:

| Capability Category | Status | Toelichting |
| :--- | :--- | :--- |
| **Discovery Coverage** | **Partial** | Cryptome raw archive ondersteund; Tor, Git-hosts, Telegram/Paste indices ontbreken. |
| **Search & Triage** | **Missing** | Geen full-text search, geen opslagen zoekopdrachten, geen watchlists of hash-filtering. |
| **Provenance** | **Partial** | Immutable observations worden opgeslagen, maar consolidatiehistorie ontbreekt. |
| **Artifact Workflow** | **Partial** | Metadata-first default ingesteld; handmatige downloadactie & quarantaine ontbreken. |
| **Multilingual/EU** | **Partial** | 27 country-packs geconfigureerd, maar entity matching is defect. |
| **Operations** | **Complete** | APScheduler, logging, en Docker Compose PostgreSQL zijn operationeel. |
| **Security** | **Complete** | SSRF guards en metadata-first default zijn correct ingesteld. |

---

## 12. Bewijs per Bevinding & 13. Reproductiestappen

### FINDING P0-01: Ontbrekende API-Routes (HTTP 404)
- **Bewijs**: Geautomatiseerde HTTP audit script gaf HTTP 404 op `/api/dashboard/summary`, `/api/artifacts/{id}`, `/api/artifacts/{id}/distributions`, `/api/artifacts/{id}/references`, `/api/artifacts/{id}/download-status`, `POST /api/artifacts/{id}/download`, `GET /api/distribution-observations`, `GET /api/reference-observations`.
- **Reproductie**:
  ```bash
  curl -i http://127.0.0.1:8000/api/dashboard/summary
  # Output: HTTP/1.1 404 Not Found {"detail":"Not Found"}
  ```

### FINDING P0-02: Silent `hasattr` Bypass op Detailpagina
- **Bewijs**: Code in `app/api/web.py` regel 69-73:
  ```python
  refs = []
  if hasattr(repo, "list_references"):
      refs = await repo.list_references(uid)
  ```
  `ArtifactDiscoveryRepository` in `app/repositories/artifact_discoveries.py` mist `list_references` en `list_acquisitions`.
- **Reproductie**: Open willekeurige `/artifacts/{artifact_id}` in browser. De secties "Referenties" en "Acquisities" tonen altijd 0 items.

### FINDING P0-03: Substring Matching Fout in Entity Matching
- **Bewijs**: `match_entities` in `app/services/artifact_entity_matching.py` evalueert `if "de" in text:`.
  Een artifact genaamd `"Trump-Orders-2025-0120.zip"` matcht land `DE` vanwege de letters `"de"` in `"Orders"`. Een file `.docx` matcht EU-entiteit `EC`.
- **Reproductie**:
  ```python
  from app.services.artifact_entity_matching import match_entities
  c, e, n = match_entities(title="Test", description=None, filename="Trump-Orders-2025.zip", locator=None, country_code="NL")
  print(c) # Output: ['DE']
  ```

### FINDING P0-04: Index- en Homepage Locators in Artifact Discoveries
- **Bewijs**: SQL query `SELECT canonical_locator FROM artifact_discoveries WHERE canonical_locator ~* 'https?://[^/]+/?$'` levert 11 records op (bijv. `https://cryptome.org/`).
- **Reproductie**:
  ```sql
  SELECT id, canonical_locator FROM artifact_discoveries WHERE canonical_locator = 'https://cryptome.org/';
  ```

---

## 14. Prioriteiten & 15. Aanbevolen Implementatievolgorde

### Aanbevolen Fasering Herstel (Remediation)
1. **Fase 1 (P0 Fixes)**:
   - Registreer ontbrekende API-routes in `app/api/artifacts.py` en `app/main.py`.
   - Voeg `list_references` en `list_acquisitions` toe aan `ArtifactDiscoveryRepository`.
   - Herstel entity matching regex met woordgrenzen (`\b`).
   - Filter homepage locators uit in `raw_archive` connector.
2. **Fase 2 (P1 Fixes)**:
   - Implementeer download status endpoint & metadata-only audit logger.
   - Herschrijf `source_stats` naar directe SQL COUNT.
   - Voeg full-text & hash zoekfilters toe aan de artifact feed.
3. **Fase 3 (P2 & Testsuite Upgrade)**:
   - Installeer `pytest-cov` en schrijf API-integratietests voor alle web/API endpoints.
   - Breng CSS-correcties aan voor lange URL-wrapping.

---

## Eindtabel Overzicht Bevindingen

| ID | Severity | Component | Finding | Evidence | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FIND-01** | **P0** | API Router | Cruciale API-routes retourneren HTTP 404 | `curl /api/dashboard/summary` -> 404 | Registreer ontbrekende endpoints in FastAPI routers |
| **FIND-02** | **P0** | Web / Repo | Detailpagina verbergt sub-resources via `hasattr` | `hasattr(repo, 'list_references')` is False | Voeg methoden toe aan `ArtifactDiscoveryRepository` |
| **FIND-03** | **P0** | Entity Service | Substring matching veroorzaakt valse land-matches | "Orders" matcht DE; "docx" matcht EC | Gebruik regex met woordgrenzen (`\b`) |
| **FIND-04** | **P0** | Connector | Homepage URL's geregistreerd als raw artifacts | 11 records in DB met locator `https://cryptome.org/` | Filter index/root URL's in connector candidate-parser |
| **FIND-05** | **P1** | Acquisition API | Download-actie & acquisitie-audit log ontbreken | `POST /api/artifacts/{id}/download` -> 404 | Bouw download endpoint dat blocked status opslaat |
| **FIND-06** | **P1** | Source API | In-memory lijst-aftapping in `source_stats` | `list_discoveries(limit=999)` in Python | Vervang door `SELECT COUNT(*)` in SQL repository |
| **FIND-07** | **P1** | Search / UI | Full-text & multi-facet zoekfunctionaliteit ontbreekt | Geen zoekbalk of hash filters op `/artifacts` | Bouw SQL ILIKE / tsvector zoek- en filterparameters |
| **FIND-08** | **P2** | Testsuite | Test coverage tool ontbreekt & nul API tests | `pytest-cov` niet geïnstalleerd; 0 API client tests | Installeer `pytest-cov` en voeg FastAPI integration tests toe |
| **FIND-09** | **P2** | Frontend UI | Tabel-kolom overflow bij lange Cryptome URL's | Horizontal scrollbar op `/artifacts` | Voeg `word-break: break-all` toe aan `app.css` |
| **FIND-10** | **P3** | Frontend UI | Paginering ontbreekt op distributies en referenties | Geen `Volgende`/`Vorige` knoppen op `/distributions` | Voeg paginering-controls toe aan templates |

---
*Einde van het Antigravity Audit Rapport.*
