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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Verify your email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f5;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 480px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 24px 40px; text-align: center; background-color: #0d1117;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                <tr>
                                    <td style="padding: 12px 24px; background-color: #00d4aa; border-radius: 12px;">
                                        <span style="font-size: 18px; font-weight: 700; color: #0d1117; letter-spacing: -0.02em;">ParityCheck</span>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 12px 0 0 0; font-size: 11px; font-weight: 600; color: #6b6b76; letter-spacing: 0.1em;">ENVGUARD</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px 40px 40px 40px;">
                            <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 700; color: #0d1117; line-height: 1.3;">
                                Verify your email
                            </h1>
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #6b6b76; line-height: 1.6;">
                                Hi {name},
                            </p>
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #25252d; line-height: 1.6;">
                                Thanks for signing up for ParityCheck. Click the button below to verify your email address and get started.
                            </p>
                            <!-- CTA Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 0 0 24px 0;">
                                        <a href="{verify_url}" style="display: inline-block; padding: 16px 32px; background-color: #00d4aa; color: #0d1117; font-size: 16px; font-weight: 600; text-decoration: none; border-radius: 12px;">
                                            Verify my email
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b6b76; line-height: 1.5;">
                                Or copy and paste this link into your browser:
                            </p>
                            <p style="margin: 0 0 24px 0; font-size: 13px;">
                                <a href="{verify_url}" style="color: #00d4aa; word-break: break-all;">{verify_url}</a>
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #6b6b76; line-height: 1.5;">
                                This link expires in 24 hours. If you didn't create an account, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #f4f4f5; border-top: 1px solid #e4e4e7; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0; font-size: 12px; color: #6b6b76; text-align: center;">
                                © ParityCheck · Environment drift detection
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    text_body = f"Hi {name},\n\nVerify your email: {verify_url}\n\nThis link expires in 24 hours.\n\nIf you didn't request this, you can ignore this email."
    await send_email(to, subject, html_body, text_body)


async def send_password_reset_email(to: str, token: str, name: str) -> bool:
    """Send password reset link."""
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
    subject = "Reset your ParityCheck password"
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Reset your password</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f5;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 480px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden;">
                    <tr>
                        <td style="padding: 40px 40px 24px 40px; text-align: center; background-color: #0d1117;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                <tr>
                                    <td style="padding: 12px 24px; background-color: #00d4aa; border-radius: 12px;">
                                        <span style="font-size: 18px; font-weight: 700; color: #0d1117;">ParityCheck</span>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 12px 0 0 0; font-size: 11px; font-weight: 600; color: #6b6b76;">ENVGUARD</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px 40px 40px 40px;">
                            <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: 700; color: #0d1117;">Reset your password</h1>
                            <p style="margin: 0 0 24px 0; font-size: 16px; color: #6b6b76;">Hi {name},</p>
                            <p style="margin: 0 0 32px 0; font-size: 16px; color: #25252d;">We received a request to reset your password. Click the button below to choose a new one.</p>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center" style="padding: 0 0 24px 0;">
                                        <a href="{reset_url}" style="display: inline-block; padding: 16px 32px; background-color: #00d4aa; color: #0d1117; font-size: 16px; font-weight: 600; text-decoration: none; border-radius: 12px;">Reset password</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b6b76;">Or copy this link: <a href="{reset_url}" style="color: #00d4aa; word-break: break-all;">{reset_url}</a></p>
                            <p style="margin: 0; font-size: 13px; color: #6b6b76;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 24px 40px; background-color: #f4f4f5; border-top: 1px solid #e4e4e7;">
                            <p style="margin: 0; font-size: 12px; color: #6b6b76; text-align: center;">© ParityCheck · Environment drift detection</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    text_body = f"Hi {name},\n\nReset your password: {reset_url}\n\nThis link expires in 1 hour.\n\nIf you didn't request this, you can ignore this email."
    await send_email(to, subject, html_body, text_body)
