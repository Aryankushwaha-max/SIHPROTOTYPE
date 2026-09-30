# eRTMAC-NWIS — Nearby Wells Intelligence System

An AI-assisted offset-well knowledge and decision-support prototype for drilling teams. NWIS brings nearby wells, structured event records, searchable DDR excerpts, historical telemetry and risk-screening examples into one local dashboard.

> **Prototype / decision support only.** This repository includes public Norwegian reference data and clearly tagged synthetic controls/events. It is not an OIL production system, does not connect to eRTMAC, and must not be used to direct live operations. Validate every observation with approved field procedures and authoritative records.

## What is included

- Interactive map of 159 source-tagged wells. Find wells by ID/name, enter latitude/longitude, use device location, or click the map; nearby wells and event history update around that location.
- Event library with formation, severity, hazard, depth, source and extraction-confidence details for 200 structured records.
- Search of 1,686 non-empty Volve DDR excerpts, kept separate because the supplied extraction loses the individual well ID.
- Historical F-9A telemetry chart with the archived 619 m incident reference (not a live feed).
- Optional sample-snapshot review with transparent threshold indicators for losses, stuck pipe, flow anomalies and torque.
- FastAPI backend organized into API routers, services, schemas and SQLite repository layers.
- Document-ingestion interface with deterministic extraction for text-based files and a clear OCR/LLM integration seam.
- Bundled data: 118 FORCE 2020 well records, one Volve well record, 40 synthetic controls, 200 synthetic structured event records, 1,686 DDR excerpts and the supplied Volve telemetry CSV.
- API documentation, Dockerfile and implementation-aligned architecture notes.

## Quick start

Requirements: Python 3.11 or newer and internet access for map tiles and the Leaflet browser library. Device location is optional and only requested when you select “Use my location.” From the extracted `eRTMAC-NWIS` folder:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Interactive API docs: http://127.0.0.1:8000/docs. SQLite is initialized with the bundled dataset on first launch. If this folder contains the earlier prototype database, the app upgrades its schema, removes only the six known shipped sample wells, and imports missing reference records while preserving other stored wells/events. Set `NWIS_DATABASE_URL` to a SQLAlchemy-compatible database URL to change the database; default is `sqlite:///./nwis.db`.

### Docker

```bash
docker build -t ertmac-nwis .
docker run --rm -p 8000:8000 -v nwis-data:/app/data ertmac-nwis
```

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health/readiness check |
| GET | `/api/v1/wells` | Find wells by radius, center and/or text query |
| GET | `/api/v1/wells/{well_id}` | Well profile, trajectory and nearby events |
| GET | `/api/v1/events` | Search and filter operational events |
| GET | `/api/v1/analytics/summary` | Dataset counts and event distribution |
| GET | `/api/v1/ddrs?q=...` | Search historical DDR text without false well-location assignment |
| GET | `/api/v1/telemetry` | Read-only historical Volve F-9A sensor trace |
| POST | `/api/v1/risks/assess` | Assess a current drilling-parameter snapshot |
| POST | `/api/v1/documents/ingest` | Extract text and candidate events from uploaded text/PDF |

Interactive OpenAPI documentation is at `/docs`. See [ARCHITECTURE.md](ARCHITECTURE.md) for design and data flow, and [the bundled data notes](app/data/reference/README.md) for provenance and limitations.

## Repository layout

```text
app/
  api/            HTTP routers and dependency wiring
  core/           Configuration and application lifecycle
  data/reference/ Curated source-tagged project datasets
  db/             Database engine, ORM models, repositories
  schemas/        Request and response contracts
  services/       Geospatial, search, ingestion and risk logic
  static/         Browser dashboard (HTML/CSS/JavaScript)
  main.py         FastAPI application entry point
docs/             Architecture pointer and data dictionary
```

## Safety and limitations

Risk scores are transparent heuristic indicators, not validated predictive models. They provide no guaranteed probability and no automated operational control. Source DDR well attribution is unresolved in the supplied extraction, so those records are searchable but not joined to mapped wells. Confidence values come from the supplied extraction and are not calibrated probabilities. Before deployment, OIL should provide approved data dictionaries, coordinate-reference conventions, access controls, retention requirements, network/security constraints, model validation criteria and an operator sign-off process. Check the upstream data terms before redistributing; the supplied archive has no single license file for all datasets.

## Development

Use `ruff check app` for linting. Keep domain logic in services, persistence in repositories, and HTTP concerns in routers. Add formal migrations and automated integration coverage before evolving deployed database schemas.
