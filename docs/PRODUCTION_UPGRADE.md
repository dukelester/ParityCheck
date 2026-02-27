# ParityCheck Production Upgrade

## Implemented Features

### 1. Real Drift Engine
- **Location**: `backend/app/services/drift_engine.py`
- **Types**: runtime, dependency, environment_variable, db_schema
- **Severity**: critical (40), high (20), medium (10), low (5)
- **Health score**: `max(0, 100 - sum(severity_weights))`
- Sensitive env vars masked in drift output

### 2. Baseline Environment System
- `is_baseline` on environments; one per workspace
- `POST /api/v1/environments/{id}/set-baseline?workspace_id=`
- First environment auto-marked as baseline
- Compare new reports against latest baseline report

### 3. Severity Scoring + Health Score
- Stored on each report
- Used in drift comparison and Slack alerts

### 4. Ignore Rules
- **Table**: `ignore_rules` (workspace_id, type, key_pattern)
- **API**: `GET/POST/DELETE /api/v1/ignore-rules/`
- Supports exact match and wildcard (*)
- Applied during drift comparison

### 5. CI/CD Fail Mode
- **CLI**: `envguard check --fail-on-drift --min-severity=high`
- Fetches baseline from API, compares locally
- Exit 1 if drift severity >= threshold

### 6. Slack Alerts
- **Table**: `alerts` (workspace_id, type, config, min_severity)
- Webhook URL encrypted with Fernet
- Triggered after drift generation when severity >= alert threshold

### 7. Teams & Workspaces
- **Tables**: `workspaces`, `workspace_members`
- Roles: owner, admin, member
- All environments belong to workspace
- API keys scoped to workspace

### 8. Plan Enforcement
- **Plans**: free (2 envs, 7-day history), pro (10 envs, 90-day, Slack), enterprise
- `check_plan_limits()` before create_environment, create_alert

### 9. Encrypted Storage
- **Service**: `backend/app/services/encryption.py`
- Fernet symmetric encryption
- Encrypts: Slack webhook URLs
- `ENCRYPTION_KEY` in config (or derived from SECRET_KEY)

### 10. Real Scheduling
- **CLI**: `envguard schedule --interval=daily --env=dev --api-key=KEY --install`
- Stores config in `~/.envguard/schedule.json`
- Installs cron (Linux/macOS) or schtasks (Windows)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/workspaces/ | List workspaces |
| GET | /api/v1/workspaces/default | Get/create default workspace |
| GET | /api/v1/environments/?workspace_id= | List environments |
| POST | /api/v1/environments/{id}/set-baseline | Set baseline |
| GET | /api/v1/reports/baseline | Get latest baseline report |
| GET | /api/v1/drifts/?env=&severity= | List drifts with filters |
| GET | /api/v1/ignore-rules/?workspace_id= | List ignore rules |
| POST | /api/v1/ignore-rules/ | Create ignore rule |
| DELETE | /api/v1/ignore-rules/{id} | Delete ignore rule |
| GET | /api/v1/alerts/?workspace_id= | List alerts |
| POST | /api/v1/alerts/ | Create Slack alert |
| DELETE | /api/v1/alerts/{id} | Delete alert |

## Environment Variables

```bash
ENCRYPTION_KEY=  # Optional; 32-byte base64 for Fernet
```

## Migration

Run `init_db()` on startup. Migrations add:
- workspace_id, user_id, is_baseline to environments
- health_score to reports
- severity, key, value_a, value_b to drifts
- workspace_id to api_keys

Legacy environments (user_id, no workspace_id) are migrated on first report upload.
