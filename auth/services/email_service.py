import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int, sender_email: str, sender_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_password_reset_email(self, recipient_email: str, reset_link: str, user_name: str) -> bool:
        try:
            subject = "Password Reset Request"
            body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_name},</p>
                    <p>You have requested to reset your password. Click the link below to proceed:</p>
                    <p><a href="{reset_link}">Reset Password</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>Best regards,<br/>Auth Service Team</p>
                </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            html_part = MIMEText(body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Password reset email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {str(e)}")
            return False
    
    def send_password_changed_email(self, recipient_email: str, user_name: str) -> bool:
        try:
            subject = "Password Changed Successfully"
            body = f"""
            <html>
                <body>
                    <h2>Password Changed</h2>
                    <p>Hello {user_name},</p>
                    <p>Your password has been successfully changed.</p>
                    <p>If you did not make this change, please contact support immediately.</p>
                    <p>Best regards,<br/>Auth Service Team</p>
                </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            html_part = MIMEText(body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Password changed confirmation email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password changed email to {recipient_email}: {str(e)}")
            return False
