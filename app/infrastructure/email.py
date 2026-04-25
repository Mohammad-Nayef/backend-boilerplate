from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.common.config import settings
from app.common.utils import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class OutboundEmail:
    to_email: str
    subject: str
    text_body: str


class EmailSender(Protocol):
    def send(self, email: OutboundEmail) -> None: ...


class LoggingEmailSender:
    def send(self, email: OutboundEmail) -> None:
        logger.info(
            "Email delivery fallback for %s | subject=%s | body=%s",
            email.to_email,
            email.subject,
            email.text_body,
        )


class SmtpEmailSender:
    def send(self, email: OutboundEmail) -> None:
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM_ADDRESS
        message["To"] = email.to_email
        message["Subject"] = email.subject
        message.set_content(email.text_body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)


def build_email_sender() -> EmailSender:
    if settings.SMTP_HOST:
        return SmtpEmailSender()
    return LoggingEmailSender()
