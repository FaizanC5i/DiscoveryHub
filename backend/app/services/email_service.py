"""
Outgoing email, used for password-reset links.

Analogy: a postal clerk. The auth code hands over a letter (recipient, subject,
body) and does not care how it travels. Today the clerk either posts it through
an SMTP server or, in development, writes it on the office whiteboard.

When SMTP_HOST is empty we log the link instead of sending it. That works in
development because nobody else reads the console. In production we never log
the link: a log file is readable by far more people than the mailbox owner, so
the token would be exposed. Instead we log an error so the missing configuration
gets noticed.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("app.email")


def send_password_reset_email(to_address: str, reset_link: str) -> None:
    settings = get_settings()
    subject = "Reset your Discovery Hub password"
    body = (
        "We received a request to reset your Discovery Hub password.\n\n"
        f"Open this link to choose a new password (valid for "
        f"{settings.reset_token_minutes} minutes, one use only):\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email. Your password will not change.\n"
    )

    if not settings.smtp_host:
        if settings.is_production:
            # Do not log the link in production (see module docstring).
            logger.error("SMTP_HOST is not configured; password reset email was not sent")
            return
        # Development convenience: print the link so you can click it without an SMTP server.
        logger.warning("DEV ONLY: password reset link for %s: %s", to_address, reset_link)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to_address
    message.set_content(body)

    # Port 587 uses STARTTLS: start plain, then upgrade the connection to TLS
    # before any credentials are sent.
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
