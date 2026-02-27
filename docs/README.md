# ParityCheck Documentation

Environment drift detection for dev, staging, and production.

---

## Table of Contents

- [Overview](#overview)
- [Drift Timeline & Root Cause](#drift-timeline--root-cause)
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
| **Docker** | Image tag, digest, base image, container OS (with `--docker`) |
| **Kubernetes** | Deployments, ConfigMaps, Secrets (with `--k8s`) |

### Drift Timeline & Root Cause

When drift appears, the dashboard shows:

- **When it started** — Timestamp of the report that first showed the drift
- **Which report introduced it** — The report (deploy) that triggered the drift
- **Which dependency caused transitive change** — For transitive drifts, the direct dependency that pulled in the change (requires `pip install pipdeptree` or `pip install envguard[root-cause]`)
- **Which deploy likely triggered it** — Same as report timestamp

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
| `analyze` | Deployment risk: compare PR/branch vs prod baseline |
| `report` | Upload report to ParityCheck SaaS |
| `check` | CI/CD: compare with baseline, optionally fail on drift |
| `schedule` | Configure scheduled checks |
| `history` | List cached reports |

---

### `collect`

Gathers OS, runtime, dependencies, env vars, and DB schema hash. Results are cached in `~/.envguard/` for use by `compare` and `report`. With `--docker`, also collects image tag, digest, base image, and container OS for drift detection.

```bash
envguard collect [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--env` | `-e` | `dev` | Environment name (dev/staging/prod) |
| `--output` | `-o` | — | Write report to file instead of cache |
| `--include-secrets` | — | `false` | Include secret env vars (default: redacted) |
| `--docker` | `-d` | `false` | Collect Docker metadata (image tag, digest, base, OS) |
| `--container` | `-c` | — | Container name/ID when running on host (use with `--docker`) |
| `--k8s` | `-k` | `false` | Collect Kubernetes metadata (deployments, configmaps, secrets) |
| `--namespace` | `-n` | `default` | Kubernetes namespace (use with `--k8s`) |
| `--deployment` | — | — | Specific deployment name (default: all in namespace) |

**Examples:**

```bash
envguard collect --env=dev
envguard collect --env=staging -o report.json
envguard collect --env=prod --include-secrets

# Inside a container: collect Docker image info for drift detection
envguard collect --env=prod --docker

# On host: inspect a specific container
envguard collect --env=prod --docker --container=my-app

# Kubernetes: ConfigMaps, Secrets, Deployments (image, replicas, resources)
envguard collect --env=prod --k8s --namespace=prod
envguard collect --env=staging --k8s -n staging --deployment=my-app
```

**Docker drift** — Base image changes (Alpine → Debian), Python minor version in container, and image digest drift are high-value production risks. Use `--docker` to detect them.

**Kubernetes drift** — ConfigMap mismatch, Secret mismatch, replica count, resource limits, and deployment env vars. Use `--k8s --namespace=prod` to detect them. Requires `kubectl` and cluster access.

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

### `analyze`

Deployment risk analysis: compares your current environment (e.g. PR branch) against a target environment (e.g. prod) and outputs a deployment risk score. Use before merging or deploying to predict drift impact.

```bash
envguard analyze [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--against` | `-a` | `prod` | Environment to compare against (prod, staging, etc.) |
| `--env` | `-e` | `dev` | Current environment / branch (report from collect) |
| `--api-key` | `-k` | **Required** | API key for authentication |
| `--api-url` | `-u` | — | API base URL |
| `--file` | `-F` | — | Report file (default: use cached for --env) |
| `--output` | `-o` | `text` | Output format: `text` or `json` |
| `--fail-on-risk` | `-f` | `false` | Exit 1 if risk score >= threshold |
| `--risk-threshold` | `-t` | `50` | Risk threshold for --fail-on-risk (0-100) |

**Examples:**

```bash
# Analyze PR branch vs prod
envguard collect --env=pr-feature-xyz
envguard analyze --against=prod --env=pr-feature-xyz --api-key=pc_xxxxx

# JSON output for CI
envguard analyze --against=prod --api-key=pc_xxxxx -o json

# Fail CI if risk >= 30
envguard analyze --against=prod --api-key=pc_xxxxx -f --risk-threshold=30
```

**Output:** Deployment risk score (0-100), health score, risk level (Low/Medium/High), safe-to-deploy flag, and list of risky changes.

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
      - run: envguard collect --env=prod --docker  # add --docker for container drift
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
