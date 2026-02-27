# ParityCheck / ENVGUARD

**Detect and alert on environment drift across dev, staging, prod.**

A fullstack SaaS for environment parity monitoring: CLI data collection, backend API, and visual dashboard.

---

## Quick Start

### CLI

```bash
# Install
pip install envguard

# Collect from dev (baseline)
envguard collect --env=dev

# Collect from prod
envguard collect --env=prod

# Compare dev vs prod
envguard compare --env=prod --baseline=dev

# Upload to SaaS (requires API key)
envguard report --api-key=YOUR_API_KEY --env=dev
```

### Full Stack (Docker)

```bash
docker compose up -d
# API: http://localhost:8000
# Dashboard: http://localhost:3000
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI       │────▶│   SaaS API  │────▶│  Dashboard  │
│  envguard   │     │  (FastAPI)  │     │   (React)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────▼─────┐
                    │ PostgreSQL│
                    │  + Redis  │
                    └───────────┘
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `collect` | Gather OS, runtime, deps, env vars, DB schema hash |
| `compare` | Compare two cached reports locally |
| `report` | Upload report to ParityCheck SaaS |
| `schedule` | Configure scheduled drift checks |
| `history` | List cached reports |

See [docs/README.md](docs/README.md) for full CLI reference and options.

---

## Project Structure

| Directory | Description |
|-----------|-------------|
| `cli/` | Python CLI (Typer) – collect, compare, report |
| `backend/` | FastAPI API – reports, drift analysis, auth |
| `frontend/` | React + Tailwind dashboard |
| `docs/` | Documentation |
| `k8s/` | Kubernetes manifests |
| `.github/workflows/` | CI/CD pipelines |

---

## Local Development

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# CLI
cd cli && pip install -e . && envguard --help
```

---

## Features

- **CLI**: Collect OS, runtime, deps, env vars, DB schema hash
- **API**: Store reports, compute drift, JWT + API key auth
- **Dashboard**: Environment parity status, diffs, history, in-app docs
- **Alerts**: Slack, email, webhook (Pro/Enterprise)
- **Billing**: Stripe integration (Free / Pro / Enterprise)

---

## Documentation

- **[Full Documentation](docs/README.md)** — CLI reference, API, CI/CD, pricing
- **In-app Docs** — Dashboard includes built-in documentation

---

## License

MIT
