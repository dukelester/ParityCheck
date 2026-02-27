"""Drift detection task."""

from app.worker import celery_app


@celery_app.task
def detect_drift() -> dict:
    """Compare reports and create drift records. Called by CronJob."""
    # TODO: Query reports, compute diffs, create Drift records, send alerts
    return {"status": "ok", "drifts_found": 0}
