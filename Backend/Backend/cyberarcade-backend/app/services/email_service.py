"""
Email service for sending verification emails via SMTP.
Falls back to console logging when SMTP is not configured.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, full_name: str, token: str):
    """Send an email verification link to the user."""
    verify_url = f"{settings.FRONTEND_URL}?verify={token}"

    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 500px; margin: 0 auto; padding: 40px 20px;">
      <div style="background: #131936; border-radius: 16px; padding: 40px; color: #E7E7E0;">
        <h1 style="font-size: 24px; margin: 0 0 8px; color: #E7E7E0;">CyberArcade</h1>
        <p style="color: #6E7C89; font-size: 13px; margin: 0 0 32px;">Cybersecurity Training Platform</p>

        <h2 style="font-size: 20px; margin: 0 0 12px;">Verify Your Email</h2>
        <p style="color: #8B8B8B; font-size: 14px; line-height: 1.6; margin: 0 0 28px;">
          Hi {full_name},<br><br>
          Welcome to CyberArcade! Click the button below to verify your email address and activate your account.
        </p>

        <a href="{verify_url}"
           style="display: inline-block; background: #4E0000; color: #E7E7E0; padding: 14px 32px;
                  border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 14px;">
          Verify Email
        </a>

        <p style="color: #6E7C89; font-size: 12px; margin: 28px 0 0; line-height: 1.5;">
          Or copy this link:<br>
          <span style="color: #8B8B8B; word-break: break-all;">{verify_url}</span>
        </p>

        <hr style="border: none; border-top: 1px solid rgba(110,124,137,0.15); margin: 28px 0;">
        <p style="color: #6E7C89; font-size: 11px; margin: 0;">
          This link expires in 24 hours. If you didn't create an account, ignore this email.
        </p>
      </div>
    </div>
    """

    if not settings.smtp_enabled:
        logger.info(f"[EMAIL] SMTP not configured. Verification URL for {to_email}: {verify_url}")
        print(f"\n{'='*60}")
        print(f"  EMAIL VERIFICATION (SMTP not configured)")
        print(f"  To: {to_email}")
        print(f"  URL: {verify_url}")
        print(f"{'='*60}\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your CyberArcade account"
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], to_email, msg.as_string())

        logger.info(f"Verification email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # Don't crash registration if email fails
        print(f"\n[EMAIL ERROR] Could not send to {to_email}: {e}")
        print(f"  Verification URL: {verify_url}\n")
