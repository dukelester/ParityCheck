"""Slack alert delivery."""

import logging
from collections import Counter

import httpx

from app.services.encryption import decrypt_optional

logger = logging.getLogger(__name__)


def _format_slack_message(
    env_name: str,
    health_score: int,
    drifts: list[dict],
) -> dict:
    """Build Slack block kit message."""
    by_sev = Counter(d.get("severity") for d in drifts)
    critical = by_sev.get("critical", 0)
    high = by_sev.get("high", 0)
    medium = by_sev.get("medium", 0)
    low = by_sev.get("low", 0)

    text = (
        f"🚨 *Parity Drift Detected*\n"
        f"Environment: *{env_name}*\n"
        f"Health Score: *{health_score}*\n"
        f"Critical: {critical} | High: {high} | Medium: {medium} | Low: {low}"
    )
    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ]
    }


async def send_slack_alert(
    webhook_url: str,
    env_name: str,
    health_score: int,
    drifts: list[dict],
) -> bool:
    """Send drift alert to Slack webhook."""
    if not webhook_url:
        return False
    if webhook_url.startswith("http://") or webhook_url.startswith("https://"):
        url = webhook_url
    else:
        url = decrypt_optional(webhook_url)
    payload = _format_slack_message(env_name, health_score, drifts)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, timeout=10.0)
            r.raise_for_status()
        logger.info("Slack alert sent for env %s", env_name)
        return True
    except Exception as e:
        logger.exception("Slack alert failed: %s", e)
        return False
