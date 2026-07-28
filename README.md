# EU Leak Discovery

Lokale, productiegerichte EU-brede leak-discovery engine.

## Vereisten

- Python 3.12+
- Docker & Docker Compose
- DeepSeek API-key (optioneel voor fase 2)

## Opstarten

### 1. `.env` aanmaken

```bash
cp .env.example .env
# Pas .env aan indien nodig (database wachtwoord, DeepSeek key, etc.)
```

### 2. PostgreSQL starten

```bash
docker compose up -d postgres
# Wacht tot PostgreSQL gereed is
docker compose logs postgres --tail 5
```

### 3. Dependencies installeren

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\Activate.ps1   # Windows
pip install -e ".[dev]"
```

### 4. Migraties uitvoeren

```bash
alembic upgrade head
```

### 5. FastAPI starten

```bash
# Linux/macOS
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows (vereist SelectorEventLoop vanwege psycopg async)
python scripts/run_uvicorn.py
```

### 6. Verificatieclaim toevoegen

```bash
python scripts/create_sample_claim.py
```

### 7. API en raw feed openen

- API: http://127.0.0.1:8000/api/claims
- Raw feed: http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/health
- Claim detail: http://127.0.0.1:8000/claims/{claim_id}

### 8. Tests draaien

```bash
# Maak testdatabase aan via Docker
docker compose exec -T postgres psql -U eu_leak -d postgres -c "CREATE DATABASE eu_leak_test" 2>/dev/null || true

# Linux/macOS
TEST_DATABASE_URL="postgresql+psycopg://eu_leak:change_me@localhost:5432/eu_leak_test" pytest -v

# Windows PowerShell
$env:TEST_DATABASE_URL="postgresql+psycopg://eu_leak:change_me@localhost:5432/eu_leak_test"; pytest -v
```

### 9. Containers stoppen

```bash
docker compose down
```

## Projectstructuur

```
eu-leak-discovery/
├── app/
│   ├── api/            # FastAPI endpoints
│   ├── database/       # SQLAlchemy modellen en sessie
│   ├── repositories/   # Databasetoegang
│   ├── schemas/        # Pydantic validatie
│   ├── services/       # Bedrijfslogica
│   ├── templates/      # Jinja2 HTML
│   ├── static/         # CSS
│   └── main.py         # FastAPI app
├── migrations/         # Alembic migraties
├── scripts/            # Hulpscripts
├── tests/              # Testsuite
└── data/               # Data directory
```
