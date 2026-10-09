import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from datetime import datetime, timedelta

from auth.routes.password_reset_routes import password_reset_bp
from auth.models.password_reset_token import PasswordResetToken


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(password_reset_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestForgotPasswordEndpoint:
    """Tests for forgot password endpoint."""

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_forgot_password_success(self, mock_get_db, mock_service, client):
        """Test successful forgot password request."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_service.initiate_password_reset.return_value = (True, "Email sent")
        
        response = client.post(
            '/auth/forgot-password',
            json={'email': 'test@example.com'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert response.json['success'] is True

    @patch('auth.routes.password_reset_routes.get_db')
    def test_forgot_password_missing_email(self, mock_get_db, client):
        """Test forgot password with missing email."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.post(
            '/auth/forgot-password',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_forgot_password_invalid_email(self, mock_get_db, mock_service, client):
        """Test forgot password with invalid email format."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.post(
            '/auth/forgot-password',
            json={'email': 'invalid-email'},
            content_type='application/json'
        )
        
        assert response.status_code == 400

    @patch('auth.routes.password_reset_routes.get_db')
    def test_forgot_password_no_body(self, mock_get_db, client):
        """Test forgot password with no request body."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.post(
            '/auth/forgot-password',
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestValidateResetTokenEndpoint:
    """Tests for validate reset token endpoint."""

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_validate_token_success(self, mock_get_db, mock_service, client):
        """Test successful token validation."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_service.validate_token.return_value = (True, 1, 'test@example.com')
        
        response = client.get('/auth/validate-reset-token/valid_token')
        
        assert response.status_code == 200
        assert response.json['valid'] is True
        assert response.json['email'] == 'test@example.com'

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_validate_token_invalid(self, mock_get_db, mock_service, client):
        """Test validation of invalid token."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_service.validate_token.return_value = (False, None, None)
        
        response = client.get('/auth/validate-reset-token/invalid_token')
        
        assert response.status_code == 400
        assert response.json['valid'] is False


class TestResetPasswordEndpoint:
    """Tests for reset password endpoint."""

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_reset_password_success(self, mock_get_db, mock_service, client):
        """Test successful password reset."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_service.reset_password.return_value = (True, "Password reset successfully")
        
        response = client.post(
            '/auth/reset-password',
            json={
                'token': 'valid_token',
                'new_password': 'NewPassword123!',
                'confirm_password': 'NewPassword123!'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert response.json['success'] is True

    @patch('auth.routes.password_reset_routes.get_db')
    def test_reset_password_passwords_dont_match(self, mock_get_db, client):
        """Test password reset with mismatched passwords."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.post(
            '/auth/reset-password',
            json={
                'token': 'valid_token',
                'new_password': 'NewPassword123!',
                'confirm_password': 'DifferentPassword123!'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400

    @patch('auth.routes.password_reset_routes.get_db')
    def test_reset_password_weak_password(self, mock_get_db, client):
        """Test password reset with weak password."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.post(
            '/auth/reset-password',
            json={
                'token': 'valid_token',
                'new_password': 'weak',
                'confirm_password': 'weak'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400

    @patch('auth.routes.password_reset_routes.PasswordResetService')
    @patch('auth.routes.password_reset_routes.get_db')
    def test_reset_password_invalid_token(self, mock_get_db, mock_service, client):
        """Test password reset with invalid token."""
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        mock_service.reset_password.return_value = (False, "Invalid token")
        
        response = client.post(
            '/auth/reset-password',
            json={
                'token': 'invalid_token',
                'new_password': 'NewPassword123!',
                'confirm_password': 'NewPassword123!'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        assert response.json['success'] is False
