from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from auth.handlers.forgot_password import ForgotPasswordHandler
from auth.handlers.reset_password import ResetPasswordHandler
from auth.services.email_service import EmailService
from auth.config import Config
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize services (in a real app, these would be injected)
email_service = None
db_session = None

def init_auth_routes(app, database_session, config):
    global email_service, db_session
    db_session = database_session
    email_service = EmailService(
        smtp_host=config.SMTP_HOST,
        smtp_port=config.SMTP_PORT,
        sender_email=config.SENDER_EMAIL,
        sender_password=config.SENDER_PASSWORD
    )
    app.register_blueprint(auth_bp)

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Handle forgot password request
    Expected JSON: {"email": "user@example.com"}
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400
        
        email = data.get('email').strip().lower()
        
        # Get reset link template from config
        reset_link_template = f"{request.host_url.rstrip('/')}auth/reset-password?token={{token}}"
        
        handler = ForgotPasswordHandler(
            db_session=db_session,
            email_service=email_service,
            token_expiration_hours=24
        )
        
        result = handler.handle_forgot_password(
            email=email,
            reset_link_template=reset_link_template
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error in forgot_password endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred processing your request"
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Handle password reset with token
    Expected JSON: {"token": "reset_token", "new_password": "newpassword123"}
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('token') or not data.get('new_password'):
            return jsonify({
                "success": False,
                "message": "Token and new password are required"
            }), 400
        
        token = data.get('token').strip()
        new_password = data.get('new_password')
        
        handler = ResetPasswordHandler(
            db_session=db_session,
            email_service=email_service
        )
        
        result = handler.handle_reset_password(
            token=token,
            new_password=new_password
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred processing your request"
        }), 500
