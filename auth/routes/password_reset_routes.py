import logging
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import Session

from auth.database import get_db
from auth.schemas.password_reset_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ValidateResetTokenRequest,
    ValidateResetTokenResponse,
    PasswordResetResponse
)
from auth.services.password_reset_service import PasswordResetService
from auth.utils.validators import validate_request_body

logger = logging.getLogger(__name__)

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/auth')
limiter = Limiter(key_func=get_remote_address)


@password_reset_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")
def forgot_password():
    """Initiate password reset flow.
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Returns:
        JSON response with success status and message.
    """
    try:
        # Validate request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Parse and validate schema
        try:
            forgot_password_request = ForgotPasswordRequest(**data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Get database session
        db = next(get_db())
        
        try:
            success, message = PasswordResetService.initiate_password_reset(
                db,
                forgot_password_request.email
            )
            
            status_code = 200 if success else 400
            return jsonify({
                "success": success,
                "message": message
            }), status_code
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error in forgot_password endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred. Please try again later"
        }), 500


@password_reset_bp.route('/validate-reset-token/<token>', methods=['GET'])
def validate_reset_token(token: str):
    """Validate a password reset token.
    
    Args:
        token: Password reset token from URL parameter.
    
    Returns:
        JSON response with token validity status.
    """
    try:
        db = next(get_db())
        
        try:
            is_valid, user_id, email = PasswordResetService.validate_token(db, token)
            
            response = ValidateResetTokenResponse(
                valid=is_valid,
                message="Token is valid" if is_valid else "Token is invalid or expired",
                email=email if is_valid else None
            )
            
            status_code = 200 if is_valid else 400
            return jsonify(response.dict()), status_code
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error validating reset token: {str(e)}")
        return jsonify({
            "valid": False,
            "message": "An error occurred while validating token"
        }), 500


@password_reset_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Reset user password with valid token.
    
    Request body:
        {
            "token": "reset_token_here",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
    
    Returns:
        JSON response with success status and message.
    """
    try:
        # Validate request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Parse and validate schema
        try:
            reset_password_request = ResetPasswordRequest(**data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Get database session
        db = next(get_db())
        
        try:
            success, message = PasswordResetService.reset_password(
                db,
                reset_password_request.token,
                reset_password_request.new_password
            )
            
            status_code = 200 if success else 400
            return jsonify({
                "success": success,
                "message": message
            }), status_code
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred. Please try again later"
        }), 500
