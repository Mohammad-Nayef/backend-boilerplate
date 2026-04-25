from __future__ import annotations

from app.common.config import settings
from app.infrastructure.email import EmailSender, OutboundEmail


class AuthEmailService:
    def __init__(self, email_sender: EmailSender):
        self.email_sender = email_sender

    def send_verification_email(
        self,
        *,
        recipient_email: str,
        full_name: str,
        code: str,
    ) -> None:
        self.email_sender.send(
            OutboundEmail(
                to_email=recipient_email,
                subject="Verify your email",
                text_body=(
                    f"Hi {full_name},\n\n"
                    f"Your verification code: {code}\n\n"
                    f"This code expires in {settings.AUTH_CODE_EXPIRE_MINUTES} minutes.\n"
                    "Only the most recently requested verification code will work."
                ),
            )
        )

    def send_password_reset_email(
        self,
        *,
        recipient_email: str,
        full_name: str,
        code: str,
    ) -> None:
        self.email_sender.send(
            OutboundEmail(
                to_email=recipient_email,
                subject="Reset your password",
                text_body=(
                    f"Hi {full_name},\n\n"
                    f"Your password reset code: {code}\n\n"
                    f"This code expires in {settings.AUTH_CODE_EXPIRE_MINUTES} minutes.\n"
                    "Only the most recently requested password reset code will work."
                ),
            )
        )
