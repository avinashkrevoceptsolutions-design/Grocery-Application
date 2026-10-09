import pytest
from flask import Flask
from unittest.mock import Mock, patch, MagicMock
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['db_session'] = Mock()
    app.config['email_service'] = Mock()
    app.config['password_hasher'] = Mock()
    app.config['PASSWORD_RESET_LINK_BASE'] = 'http://localhost:3000/reset-password'
    
    from auth.routes.password_reset_routes import password_reset_bp
    app.register_blueprint(password_reset_bp)
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

class TestPasswordResetRoutes:
    
    def test_forgot_password_success(self, client, app):
        """Test successful forgot password request"""
        with app.app_context():
            mock_service = Mock()
            mock_service.request_password_reset.return_value = {
                'success': True,
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }
            
            with patch('auth.routes.password_reset_routes.PasswordResetService', return_value=mock_service):
                response = client.post('/auth/forgot-password', 
                    json={'email': 'test@example.com'},
                    content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
    
    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with invalid email"""
        response = client.post('/auth/forgot-password',
            json={'email': 'invalid-email'},
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_forgot_password_missing_email(self, client):
        """Test forgot password with missing email"""
        response = client.post('/auth/forgot-password',
            json={},
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_validate_reset_token_success(self, client, app):
        """Test successful token validation"""
        with app.app_context():
            mock_service = Mock()
            mock_service.validate_reset_token.return_value = {
                'success': True,
                'message': 'Token is valid.',
                'token_valid': True
            }
            
            with patch('auth.routes.password_reset_routes.PasswordResetService', return_value=mock_service):
                response = client.post('/auth/validate-reset-token',
                    json={'token': 'valid_token'},
                    content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['token_valid'] is True
    
    def test_validate_reset_token_invalid(self, client, app):
        """Test validation of invalid token"""
        with app.app_context():
            mock_service = Mock()
            mock_service.validate_reset_token.return_value = {
                'success': False,
                'message': 'Invalid or expired reset token.',
                'token_valid': False
            }
            
            with patch('auth.routes.password_reset_routes.PasswordResetService', return_value=mock_service):
                response = client.post('/auth/validate-reset-token',
                    json={'token': 'invalid_token'},
                    content_type='application/json')
                
                assert response.status_code == 400
                data = json.loads(response.data)
                assert data['success'] is False
                assert data['token_valid'] is False
    
    def test_reset_password_success(self, client, app):
        """Test successful password reset"""
        with app.app_context():
            mock_service = Mock()
            mock_service.reset_password.return_value = {
                'success': True,
                'message': 'Your password has been reset successfully. Please log in with your new password.'
            }
            
            with patch('auth.routes.password_reset_routes.PasswordResetService', return_value=mock_service):
                response = client.post('/auth/reset-password',
                    json={
                        'token': 'valid_token',
                        'new_password': 'NewPassword123!',
                        'confirm_password': 'NewPassword123!'
                    },
                    content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
    
    def test_reset_password_passwords_not_matching(self, client):
        """Test password reset with non-matching passwords"""
        response = client.post('/auth/reset-password',
            json={
                'token': 'valid_token',
                'new_password': 'NewPassword123!',
                'confirm_password': 'DifferentPassword123!'
            },
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_reset_password_weak_password(self, client):
        """Test password reset with weak password"""
        response = client.post('/auth/reset-password',
            json={
                'token': 'valid_token',
                'new_password': 'weak',
                'confirm_password': 'weak'
            },
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_reset_password_missing_fields(self, client):
        """Test password reset with missing fields"""
        response = client.post('/auth/reset-password',
            json={'token': 'valid_token'},
            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False