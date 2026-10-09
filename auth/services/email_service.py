import logging
from typing import Optional
from flask_mail import Mail, Message
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self, mail: Mail):
        self.mail = mail
    
    def send_password_reset_email(self, recipient_email: str, reset_link: str) -> bool:
        """Send password reset email to user"""
        try:
            subject = 'Password Reset Request'
            
            html_body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>You have requested to reset your password. Click the link below to proceed:</p>
                    <p><a href="{reset_link}">Reset Your Password</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <hr>
                    <p><small>Do not share this link with anyone.</small></p>
                </body>
            </html>
            """
            
            text_body = f"""
            Password Reset Request
            
            You have requested to reset your password. Visit the link below to proceed:
            {reset_link}
            
            This link will expire in 24 hours.
            
            If you did not request this, please ignore this email.
            
            Do not share this link with anyone.
            """
            
            message = Message(
                subject=subject,
                recipients=[recipient_email],
                html=html_body,
                body=text_body
            )
            
            self.mail.send(message)
            logger.info(f'Password reset email sent to: {recipient_email}')
            return True
        
        except Exception as e:
            logger.error(f'Error sending password reset email to {recipient_email}: {str(e)}')
            return False