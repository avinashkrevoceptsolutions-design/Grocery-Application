from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import Optional
import logging

from auth.services.password_reset_service import PasswordResetService
from auth.services.email_service import EmailService
from auth.middleware.rate_limiter import rate_limit
from auth.models.user import User
from auth.utils.validation import validate_email, validate_password

logger = logging.getLogger(__name__)

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/auth')

# These will be injected via dependency injection
db_session: Optional[Session] = None
email_service: Optional[EmailService] = None


def init_password_reset_routes(
    app,
    database_session: Session,
    mail_service: EmailService
):
    """
    Initialize password reset routes with dependencies.
    
    Args:
        app: Flask application
        database_session: SQLAlchemy database session
        mail_service: Email service instance
    """
    global db_session, email_service
    db_session = database_session
    email_service = mail_service
    app.register_blueprint(password_reset_bp)


@password_reset_bp.route('/forgot-password', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=3600)
def forgot_password():
    """
    Request a password reset.
    
    Expected JSON:
    {
        "email": "user@example.com"
    }
    
    Returns:
        Success/error message (same response for valid/invalid emails to prevent user enumeration)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request format'
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'error': 'Email is required'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format'
            }), 400
        
        # Check if user exists (but don't reveal whether email exists)
        user = db_session.query(User).filter(
            User.email == email
        ).first()
        
        # Always return success message to prevent user enumeration
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return jsonify({
                'message': 'If an account exists with this email, password reset instructions have been sent.'
            }), 200
        
        # Generate and send reset token
        password_reset_service = PasswordResetService(
            db_session=db_session,
            email_service=email_service
        )
        
        success, message = password_reset_service.generate_reset_token(
            user_id=user.id,
            email=email
        )
        
        # Always return success message
        return jsonify({
            'message': 'If an account exists with this email, password reset instructions have been sent.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in forgot_password endpoint: {str(e)}")
        return jsonify({
            'error': 'An error occurred. Please try again later.'
        }), 500


@password_reset_bp.route('/reset-password/validate/<token>', methods=['GET'])
def validate_reset_token(token: str):
    """
    Validate a password reset token.
    
    Returns:
        User info if valid, error message if invalid
    """
    try:
        if not token:
            return jsonify({
                'error': 'Reset token is required'
            }), 400
        
        password_reset_service = PasswordResetService(
            db_session=db_session,
            email_service=email_service
        )
        
        is_valid, user_info = password_reset_service.validate_token(token)
        
        if not is_valid:
            return jsonify({
                'error': 'Invalid or expired reset token'
            }), 400
        
        return jsonify({
            'valid': True,
            'user_info': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating reset token: {str(e)}")
        return jsonify({
            'error': 'An error occurred while validating token'
        }), 500


@password_reset_bp.route('/reset-password', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=3600)
def reset_password():
    """
    Confirm password reset with new password.
    
    Expected JSON:
    {
        "token": "reset_token_string",
        "password": "new_password",
        "password_confirm": "new_password"
    }
    
    Returns:
        Success/error message
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request format'
            }), 400
        
        token = data.get('token', '').strip()
        password = data.get('password', '')
        password_confirm = data.get('password_confirm', '')
        
        # Validate input
        if not token:
            return jsonify({
                'error': 'Reset token is required'
            }), 400
        
        if not password or not password_confirm:
            return jsonify({
                'error': 'Password is required'
            }), 400
        
        if password != password_confirm:
            return jsonify({
                'error': 'Passwords do not match'
            }), 400
        
        # Validate password strength
        is_valid, validation_message = validate_password(password)
        if not is_valid:
            return jsonify({
                'error': validation_message
            }), 400
        
        # Reset password
        password_reset_service = PasswordResetService(
            db_session=db_session,
            email_service=email_service
        )
        
        success, message = password_reset_service.reset_password(
            token=token,
            new_password=password
        )
        
        if not success:
            return jsonify({
                'error': message
            }), 400
        
        logger.info(f"Password reset completed successfully")
        
        return jsonify({
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {str(e)}")
        return jsonify({
            'error': 'An error occurred while resetting password'
        }), 500