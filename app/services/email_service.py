import logging
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.mail_from = settings.MAIL_FROM
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def send_password_reset_email(self, email: str, reset_token: Optional[str] = None) -> bool:
        """Send password reset email to user"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.mail_from]):
            logger.warning("SMTP configuration incomplete. Email service disabled.")
            return False

        try:
            # Create reset link - frontend should handle token parameter
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}" if reset_token and settings.FRONTEND_URL else "[Password Reset Link]"
            
            subject = "Password Reset Request"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                    .footer {{ background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 12px; border-radius: 0 0 5px 5px; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                    .warning {{ color: #d9534f; font-weight: bold; }}
                    .expires {{ color: #666; font-size: 14px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>We received a request to reset the password for your account associated with this email address.</p>
                        <p>Click the button below to reset your password:</p>
                        <a href="{reset_link}" class="button">Reset Password</a>
                        <p>Or copy and paste this link in your browser:</p>
                        <p>{reset_link}</p>
                        <p class="expires">⏱️ This link will expire in <strong>15 minutes</strong>.</p>
                        <p class="warning">⚠️ If you did not request a password reset, please ignore this email or contact support immediately.</p>
                        <p>For security reasons, never share this link with anyone.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 Our Service. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Send email asynchronously
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._send_smtp_email,
                email,
                subject,
                html_content
            )
            return result

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False

    def _send_smtp_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP (blocking operation)"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.mail_from
            message["To"] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(f"Password reset email sent to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {str(e)}")
            return False


email_service = EmailService()