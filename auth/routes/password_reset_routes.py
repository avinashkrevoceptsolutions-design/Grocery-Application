from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError
from sqlalchemy.orm import Session
from auth.schemas.password_reset_schema import (
    ForgotPasswordSchema,
    ValidateResetTokenSchema,
    ResetPasswordSchema
)
from auth.services.password_reset_service import PasswordResetService
from auth.services.email_service import EmailService
from auth.utils.token_generator import TokenGenerator
import logging

logger = logging.getLogger(__name__)

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/auth')
limiter = Limiter(key_func=get_remote_address)

@password_reset_bp.route('/forgot-password', methods=['POST'])
@limiter.limit('5 per hour')
def forgot_password():
    """
    Request a password reset token
    POST /auth/forgot-password
    Body: {"email": "user@example.com"}
    """
    try:
        schema = ForgotPasswordSchema()
        data = schema.load(request.get_json())
        
        db = current_app.config.get('db_session')
        email_service = current_app.config.get('email_service')
        
        password_reset_service = PasswordResetService(db, email_service)
        
        reset_link_base = current_app.config.get('PASSWORD_RESET_LINK_BASE', 'http://localhost:3000/reset-password')
        result = password_reset_service.request_password_reset(data['email'], reset_link_base)
        
        return jsonify(result), 200 if result['success'] else 400
    
    except ValidationError as e:
        logger.warning(f'Validation error in forgot_password: {e.messages}')
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages
        }), 400
    
    except Exception as e:
        logger.error(f'Error in forgot_password: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request.'
        }), 500

@password_reset_bp.route('/validate-reset-token', methods=['POST'])
def validate_reset_token():
    """
    Validate a password reset token
    POST /auth/validate-reset-token
    Body: {"token": "reset_token_value"}
    """
    try:
        schema = ValidateResetTokenSchema()
        data = schema.load(request.get_json())
        
        db = current_app.config.get('db_session')
        email_service = current_app.config.get('email_service')
        
        password_reset_service = PasswordResetService(db, email_service)
        result = password_reset_service.validate_reset_token(data['token'])
        
        return jsonify(result), 200 if result['success'] else 400
    
    except ValidationError as e:
        logger.warning(f'Validation error in validate_reset_token: {e.messages}')
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages,
            'token_valid': False
        }), 400
    
    except Exception as e:
        logger.error(f'Error in validate_reset_token: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while validating the token.',
            'token_valid': False
        }), 500

@password_reset_bp.route('/reset-password', methods=['POST'])
@limiter.limit('5 per hour')
def reset_password():
    """
    Reset password with valid token
    POST /auth/reset-password
    Body: {"token": "reset_token_value", "new_password": "NewPass123!", "confirm_password": "NewPass123!"}
    """
    try:
        schema = ResetPasswordSchema()
        data = schema.load(request.get_json())
        
        db = current_app.config.get('db_session')
        email_service = current_app.config.get('email_service')
        password_hasher = current_app.config.get('password_hasher')
        
        password_reset_service = PasswordResetService(db, email_service)
        result = password_reset_service.reset_password(data['token'], data['new_password'], password_hasher)
        
        return jsonify(result), 200 if result['success'] else 400
    
    except ValidationError as e:
        logger.warning(f'Validation error in reset_password: {e.messages}')
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': e.messages
        }), 400
    
    except Exception as e:
        logger.error(f'Error in reset_password: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while resetting your password.'
        }), 500