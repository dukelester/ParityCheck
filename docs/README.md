# ParityCheck Documentation

Environment drift detection for dev, staging, and production.

---

## Table of Contents

- [Overview](#overview)
- [CLI Reference](#cli-reference)
- [Dashboard](#dashboard)
- [API](#api)
- [CI/CD Integration](#cicd-integration)
- [Pricing & Plans](#pricing--plans)

---

## Overview

ParityCheck helps teams detect and alert on environment drift. When dev, staging, and production diverge, you get:

- **Dependency mismatches** — Different package versions across environments
- **Config drift** — Environment variable differences
- **Schema drift** — Database schema changes

The **envguard** CLI collects metadata from your environments and uploads it to the SaaS dashboard for comparison, alerts, and historical tracking.

### What Gets Collected

| Category | Description |
|----------|-------------|
| **OS** | System, release, version, machine |
| **Runtime** | Python version, executable path |
| **Dependencies** | All pip-installed packages and versions |
| **Env vars** | Environment variables (secrets redacted by default) |
| **DB schema** | Hash of database schema (when configured) |

---

## CLI Reference

### Installation

```bash
pip install envguard
```

Or from source:

```bash
cd cli && pip install -e .
```

### Commands

| Command | Description |
|---------|-------------|
| `collect` | Gather metadata from current environment |
| `compare` | Compare two cached reports locally |
| `report` | Upload report to ParityCheck SaaS |
| `schedule` | Configure scheduled checks |
| `history` | List cached reports |

---

### `collect`

Gathers OS, runtime, dependencies, env vars, and DB schema hash. Results are cached in `~/.envguard/` for use by `compare` and `report`.

```bash
envguard collect [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--env` | `-e` | `dev` | Environment name (dev/staging/prod) |
| `--output` | `-o` | — | Write report to file instead of cache |
| `--include-secrets` | — | `false` | Include secret env vars (default: redacted) |

**Examples:**

```bash
envguard collect --env=dev
envguard collect --env=staging -o report.json
envguard collect --env=prod --include-secrets
```

---

### `compare`

Compares two locally cached reports. Shows added, removed, and changed keys for dependencies and env vars.

```bash
envguard compare [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--env` | `-e` | `prod` | Environment to compare |
| `--baseline` | `-b` | `dev` | Baseline environment |

**Examples:**

```bash
# Compare prod against dev
envguard compare --env=prod

# Compare staging against prod
envguard compare --env=staging --baseline=prod
```

---

### `report`

Uploads the cached report to the ParityCheck SaaS API. Requires an API key from the dashboard.

```bash
envguard report [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--api-key` | `-k` | **Required** | API key for authentication |
| `--env` | `-e` | `dev` | Environment name |
| `--api-url` | `-u` | `https://api.paritycheck.io` | API base URL |
| `--file` | `-f` | — | Report file (default: use cached) |

**Examples:**

```bash
envguard report --api-key=pc_xxxxx --env=dev
envguard report --api-key=pc_xxxxx -f ./report.json --env=prod
envguard report --api-key=pc_xxxxx --api-url=https://parity.internal/api
```

---

### `schedule`

Configures scheduled drift checks. For full automation, use a CI cron job or the SaaS dashboard (Pro/Enterprise).

```bash
envguard schedule [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--interval` | `-i` | `daily` | `hourly` \| `daily` \| `weekly` |
| `--notify` | `-n` | `false` | Enable Slack/email alerts |
| `--api-key` | `-k` | — | Required when `--notify` |

---

### `history`

Lists locally cached reports in `~/.envguard/`.

```bash
envguard history [OPTIONS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--env` | `-e` | Filter by environment |

---

## Dashboard

The dashboard provides:

- **Overview** — Environment parity status at a glance
- **Drifts** — Active drift records with type, environment, and details
- **History** — Report history and trends (when connected)

### Getting an API Key

1. Sign up at [paritycheck.io](https://paritycheck.io)
2. Create an API key in Settings
3. Use it with `envguard report --api-key=YOUR_KEY`

---

## API

The ParityCheck API is RESTful.

### Base URL

```
https://api.paritycheck.io
```

### Authentication

- **API Key**: `X-API-Key: pc_xxxxx` or `Authorization: Bearer pc_xxxxx`
- **JWT**: `Authorization: Bearer <token>` (for dashboard)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/reports` | Upload report |
| `GET` | `/api/v1/reports/{id}` | Get report |
| `GET` | `/api/v1/environments` | List environments |
| `GET` | `/api/v1/drifts` | List drifts |

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Parity Check
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install envguard
      - run: envguard collect --env=prod
      - run: envguard report --api-key=${{ secrets.PARITYCHECK_API_KEY }} --env=prod
```

### GitLab CI

```yaml
parity-check:
  image: python:3.12-slim
  script:
    - pip install envguard
    - envguard collect --env=prod
    - envguard report --api-key=$PARITYCHECK_API_KEY --env=prod
  only:
    - schedules
```

---

## Pricing & Plans

| Plan | Free | Pro | Enterprise |
|------|------|-----|------------|
| Environments | 3 | 10 | Unlimited |
| Reports/month | 100 | 1,000 | Unlimited |
| Alerts | — | ✓ | ✓ |
| Team access | — | 5 | Unlimited |
| Audit logs | — | ✓ | ✓ |
| SLA | — | — | ✓ |

---

## Support

- [GitHub Issues](https://github.com/paritycheck/envguard/issues)
- [Documentation](https://paritycheck.io/docs)
