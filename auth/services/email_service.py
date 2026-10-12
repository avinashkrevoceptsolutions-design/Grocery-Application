import logging
from typing import Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls
    
    def send_password_reset_email(
        self,
        email: str,
        reset_url: str,
        expiry_hours: int = 24
    ) -> bool:
        """
        Send password reset email to user.
        
        Args:
            email: Recipient email address
            reset_url: URL for password reset link
            expiry_hours: Hours until reset token expires
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = "Password Reset Request"
            
            # HTML content
            html_body = self._render_html_template(
                template_name='password_reset_email.html',
                reset_url=reset_url,
                expiry_hours=expiry_hours
            )
            
            # Plain text content
            text_body = self._render_text_template(
                template_name='password_reset_email.txt',
                reset_url=reset_url,
                expiry_hours=expiry_hours
            )
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            return False
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML version of email body
            text_body: Plain text version of email body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # Attach both text and html versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            if self.use_tls:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
            
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _render_html_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        Render HTML email template.
        
        Args:
            template_name: Name of template file
            **kwargs: Variables to pass to template
            
        Returns:
            Rendered HTML content
        """
        try:
            # In production, use proper template loading
            # For now, return a basic template
            reset_url = kwargs.get('reset_url', '')
            expiry_hours = kwargs.get('expiry_hours', 24)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ color: #333; margin-bottom: 20px; }}
                    .content {{ color: #666; line-height: 1.6; }}
                    .button {{
                        display: inline-block;
                        background-color: #007bff;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 20px 0;
                    }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Password Reset Request</h2>
                    </div>
                    <div class="content">
                        <p>We received a request to reset your password. Click the button below to proceed:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>This link will expire in {expiry_hours} hours.</p>
                        <p>If you didn't request this, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 Your App. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return html_content
            
        except Exception as e:
            logger.error(f"Error rendering HTML template: {str(e)}")
            return ""
    
    def _render_text_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        Render plain text email template.
        
        Args:
            template_name: Name of template file
            **kwargs: Variables to pass to template
            
        Returns:
            Rendered text content
        """
        try:
            reset_url = kwargs.get('reset_url', '')
            expiry_hours = kwargs.get('expiry_hours', 24)
            
            text_content = f"""
Password Reset Request

We received a request to reset your password. Use the link below to proceed:

{reset_url}

This link will expire in {expiry_hours} hours.

If you didn't request this, please ignore this email.

---
© 2024 Your App. All rights reserved.
            """
            return text_content
            
        except Exception as e:
            logger.error(f"Error rendering text template: {str(e)}")
            return ""