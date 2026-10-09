import logging
from typing import Optional
from flask_mail import Mail, Message
from flask import current_app, render_template_string

logger = logging.getLogger(__name__)

mail = Mail()


class EmailService:
    """Service for sending email notifications."""

    @staticmethod
    def send_password_reset_email(email: str, token: str, user_name: Optional[str] = None) -> bool:
        """Send password reset email with token.
        
        Args:
            email: Recipient email address.
            token: Password reset token.
            user_name: Optional user name for personalization.
            
        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        try:
            reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
            
            subject = "Password Reset Request"
            
            html_body = render_template_string(
                """
                <html>
                    <body>
                        <h2>Password Reset Request</h2>
                        <p>Hello {{ user_name or 'User' }},</p>
                        <p>We received a request to reset your password. Click the link below to proceed:</p>
                        <p><a href="{{ reset_url }}">Reset Password</a></p>
                        <p>This link will expire in 24 hours.</p>
                        <p>If you did not request this, please ignore this email.</p>
                        <p>Best regards,<br>The Auth Team</p>
                    </body>
                </html>
                """,
                reset_url=reset_url,
                user_name=user_name
            )
            
            text_body = f"""Password Reset Request

Hello {user_name or 'User'},

We received a request to reset your password. Visit the link below to proceed:
{reset_url}

This link will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
The Auth Team
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_confirmation_email(email: str, user_name: Optional[str] = None) -> bool:
        """Send password reset confirmation email.
        
        Args:
            email: Recipient email address.
            user_name: Optional user name for personalization.
            
        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        try:
            subject = "Password Reset Successful"
            
            html_body = render_template_string(
                """
                <html>
                    <body>
                        <h2>Password Reset Successful</h2>
                        <p>Hello {{ user_name or 'User' }},</p>
                        <p>Your password has been successfully reset.</p>
                        <p>You can now log in with your new password.</p>
                        <p>If you did not make this change, please contact support immediately.</p>
                        <p>Best regards,<br>The Auth Team</p>
                    </body>
                </html>
                """,
                user_name=user_name
            )
            
            text_body = f"""Password Reset Successful

Hello {user_name or 'User'},

Your password has been successfully reset.
You can now log in with your new password.

If you did not make this change, please contact support immediately.

Best regards,
The Auth Team
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            logger.info(f"Password reset confirmation email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset confirmation email to {email}: {str(e)}")
            return False
