"""Email sending service."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    """Send an email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.DEV_SKIP_EMAIL:
            logger.info("DEV_SKIP_EMAIL: Would send to %s - %s", to, subject)
            logger.info("Link/body: %s", (text_body or html_body)[:500])
            return True
        # Port 587: STARTTLS (use_tls=False, start_tls=True for Gmail)
        # Port 465: Implicit TLS (use_tls=True)
        use_tls = settings.SMTP_PORT == 465
        start_tls = settings.SMTP_PORT == 587
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        logger.info("Email sent to %s", to)
        return True
    except Exception as e:
        logger.exception("Email send failed: %s", e)
        raise


async def send_verification_email(to: str, token: str, name: str) -> bool:
    """Send email verification link."""
    verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
    subject = "Verify your ParityCheck email"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #06b6d4;">Verify your email</h2>
        <p>Hi {name},</p>
        <p>Thanks for signing up for ParityCheck. Click the button below to verify your email address:</p>
        <p style="margin: 24px 0;">
            <a href="{verify_url}" style="background: #06b6d4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Verify Email</a>
        </p>
        <p>Or copy this link: <a href="{verify_url}">{verify_url}</a></p>
        <p style="color: #71717a; font-size: 14px;">This link expires in 24 hours. If you didn't create an account, you can ignore this email.</p>
        <p>— ParityCheck</p>
    </body>
    </html>
    """
    text_body = f"Hi {name},\n\nVerify your email: {verify_url}\n\nThis link expires in 24 hours.\n\nIf you didn't request this, you can ignore this email."
    await send_email(to, subject, html_body, text_body)
