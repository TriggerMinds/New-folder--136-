# Architectuur Blauwdruk

## Doelstelling

Bouw een lokaal draaiende, productiegerichte EU-brede leak-discovery engine die openbare online bronnen monitort en nieuwe leak-signalen uit alle 27 EU-lidstaten detecteert, registreert, structureert, dedupliceert en doorzoekbaar maakt.

Iedere publiek waarneembare leak-claim wordt eerst geregistreerd als `observed_leak_claim`.

Registratie mag niet afhankelijk zijn van bronreputatie, politieke gevoeligheid, inhoudelijke relevantie, internationale media-aandacht, authenticiteitsbeoordeling of AI-classificatie.

Verificatie, authenticiteit, provenance en context worden uitsluitend als aanvullende metadata opgeslagen. Deze velden mogen registratie of zichtbaarheid niet blokkeren.

## Systeem Topologie

```text
eu-leak-discovery/
├── .env.example
├── .gitignore
├── README.md
├── architectuur_blauwdruk.md
├── PROJECTSPECIFICATIES.md
├── KILO_CODE_STARTPROMPT.md
├── pyproject.toml
├── docker-compose.yml
├── alembic.ini
├── app/
├── migrations/
├── scripts/
├── data/
└── tests/
```

## Hardware Context

```text
Windows Subsystem for Linux
WSL Ubuntu
maximaal 8GB VRAM
```

Geen lokale LLM's, geen GPU-inference, geen zware browserclusters, geen microservices en geen OpenSearch tenzij PostgreSQL aantoonbaar tekortschiet.

## Executie Parameters

Kilo Code moet ieder bestand volledig genereren.

Verboden:

```text
placeholders
TODO-blokken zonder implementatie
pseudocode
ingekorte imports
lege method bodies
NotImplementedError als placeholder
ellipsis
```

Functionele prioriteit:

```text
1. Werkende ingestie
2. Permanente lokale opslag
3. Chronologische raw feed
4. Bronstatus
5. Deduplicatie
6. DeepSeek-enrichment
7. Zoeken en filters
8. Export
9. Aanvullende connectortypen
```

DeepSeek-fouten leiden tot `ai_enrichment_status = pending` en mogen ingestie nooit blokkeren.

Minimale runtime:

```text
Python 3.12+
FastAPI
Uvicorn
PostgreSQL
SQLAlchemy
Alembic
APScheduler
HTTPX
BeautifulSoup4
Trafilatura
Feedparser
PyYAML
Pydantic
Jinja2
HTMX
python-dotenv
DeepSeek API
```

Niet opnemen zonder expliciete noodzaak:

```text
OpenSearch
Elasticsearch
Redis
Celery
Kafka
Kubernetes
Prometheus
Grafana
React
Next.js
lokale taalmodellen
vector databases
microservices
```

Acceptatiecriteria:

```text
De applicatie start lokaal vanuit WSL Ubuntu.
PostgreSQL wordt automatisch bereikbaar via Docker Compose.
Database-migraties worden uitgevoerd.
De webinterface opent lokaal.
RSS- en HTML-connectors functioneren.
Nieuwe observaties worden permanent opgeslagen.
Iedere observatie verschijnt direct in de raw feed.
Claims gebruiken observed_leak_claim.
Exacte URL- en contentduplicaten worden gekoppeld.
DeepSeek Flash verrijkt claims via de API-key.
DeepSeek-uitval blokkeert ingestie niet.
Zoeken werkt op land, taal, instelling, dossier, host en datum.
JSONL- en CSV-export functioneren.
Alle 27 country-packmappen bestaan en worden gevalideerd.
Er zijn geen placeholders, mocks of ingekorte bestanden.
```
