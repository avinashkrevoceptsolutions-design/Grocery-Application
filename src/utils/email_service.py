import logging
from typing import Optional
from abc import ABC, abstractmethod
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base class for email service."""

    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_link: str, user_name: str) -> bool:
        """Send password reset email."""
        pass

    @abstractmethod
    async def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send generic email."""
        pass


class SMTPEmailService(EmailServiceBase):
    """Email service using SMTP."""

    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, from_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

    async def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Attach plain text part
            message.attach(MIMEText(body, "plain"))

            # Attach HTML part if provided
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.sendmail(self.from_email, to_email, message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_password_reset_email(self, email: str, reset_link: str, user_name: str) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User email address
            reset_link: Password reset link
            user_name: User's name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Password Reset Request"
        body = f"""Hello {user_name},

You have requested to reset your password. Please click the link below to reset your password:

{reset_link}

This link will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
The Auth Team"""

        html_body = f"""<html>
<body>
<p>Hello {user_name},</p>
<p>You have requested to reset your password. Please click the link below to reset your password:</p>
<p><a href="{reset_link}">Reset Password</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you did not request this, please ignore this email.</p>
<p>Best regards,<br>The Auth Team</p>
</body>
</html>"""

        return await self.send_email(email, subject, body, html_body)


class MockEmailService(EmailServiceBase):
    """Mock email service for testing."""

    def __init__(self):
        self.sent_emails = []

    async def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Mock send email."""
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "body": body,
            "html_body": html_body
        })
        logger.info(f"Mock email sent to {to_email}")
        return True

    async def send_password_reset_email(self, email: str, reset_link: str, user_name: str) -> bool:
        """Mock send password reset email."""
        subject = "Password Reset Request"
        body = f"Reset link: {reset_link}"
        return await self.send_email(email, subject, body)


def get_email_service() -> EmailServiceBase:
    """Factory function to get email service based on configuration."""
    if settings.EMAIL_BACKEND == "mock":
        return MockEmailService()
    else:
        return SMTPEmailService(
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
            from_email=settings.FROM_EMAIL
        )
