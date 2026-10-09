import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from auth.services.password_reset_service import PasswordResetService
from auth.models.user import User
from auth.models.password_reset_token import PasswordResetToken
from auth.utils.token_generator import TokenGenerator

class TestPasswordResetService:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_email_service(self):
        return Mock()
    
    @pytest.fixture
    def password_reset_service(self, mock_db, mock_email_service):
        return PasswordResetService(mock_db, mock_email_service)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.email = 'test@example.com'
        user.username = 'testuser'
        user.password_reset_attempts = 0
        user.password_reset_last_attempt = None
        return user
    
    def test_request_password_reset_success(self, password_reset_service, mock_db, mock_email_service, mock_user):
        """Test successful password reset request"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_email_service.send_password_reset_email.return_value = True
        
        result = password_reset_service.request_password_reset('test@example.com', 'http://localhost:3000/reset')
        
        assert result['success'] is True
        assert 'password reset link has been sent' in result['message']
        mock_email_service.send_password_reset_email.assert_called_once()
    
    def test_request_password_reset_user_not_found(self, password_reset_service, mock_db):
        """Test password reset request for non-existent user"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = password_reset_service.request_password_reset('nonexistent@example.com', 'http://localhost:3000/reset')
        
        assert result['success'] is True
        assert 'If an account exists' in result['message']
    
    def test_request_password_reset_rate_limited(self, password_reset_service, mock_db, mock_user):
        """Test password reset request when rate limited"""
        mock_user.password_reset_attempts = 5
        mock_user.password_reset_last_attempt = datetime.utcnow() - timedelta(minutes=30)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = password_reset_service.request_password_reset('test@example.com', 'http://localhost:3000/reset')
        
        assert result['success'] is False
        assert 'Too many' in result['message']
    
    def test_validate_reset_token_valid(self, password_reset_service, mock_db):
        """Test validation of valid reset token"""
        token = TokenGenerator.generate_token()
        token_hash = TokenGenerator.hash_token(token)
        
        mock_reset_token = Mock(spec=PasswordResetToken)
        mock_reset_token.token = token_hash
        mock_reset_token.is_valid.return_value = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_reset_token
        
        result = password_reset_service.validate_reset_token(token)
        
        assert result['success'] is True
        assert result['token_valid'] is True
    
    def test_validate_reset_token_invalid(self, password_reset_service, mock_db):
        """Test validation of invalid reset token"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = password_reset_service.validate_reset_token('invalid_token')
        
        assert result['success'] is False
        assert result['token_valid'] is False
    
    def test_validate_reset_token_expired(self, password_reset_service, mock_db):
        """Test validation of expired reset token"""
        token = TokenGenerator.generate_token()
        token_hash = TokenGenerator.hash_token(token)
        
        mock_reset_token = Mock(spec=PasswordResetToken)
        mock_reset_token.token = token_hash
        mock_reset_token.is_valid.return_value = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_reset_token
        
        result = password_reset_service.validate_reset_token(token)
        
        assert result['success'] is False
        assert result['token_valid'] is False
    
    def test_reset_password_success(self, password_reset_service, mock_db, mock_user):
        """Test successful password reset"""
        token = TokenGenerator.generate_token()
        token_hash = TokenGenerator.hash_token(token)
        
        mock_reset_token = Mock(spec=PasswordResetToken)
        mock_reset_token.token = token_hash
        mock_reset_token.user_id = 1
        mock_reset_token.is_valid.return_value = True
        
        mock_password_hasher = Mock()
        mock_password_hasher.hash.return_value = 'hashed_password'
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_reset_token, mock_user]
        
        result = password_reset_service.reset_password(token, 'NewPassword123!', mock_password_hasher)
        
        assert result['success'] is True
        assert 'password has been reset successfully' in result['message']
        mock_reset_token.mark_as_used.assert_called_once()
    
    def test_reset_password_invalid_token(self, password_reset_service, mock_db):
        """Test password reset with invalid token"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_password_hasher = Mock()
        
        result = password_reset_service.reset_password('invalid_token', 'NewPassword123!', mock_password_hasher)
        
        assert result['success'] is False
        assert 'Invalid or expired' in result['message']
    
    def test_reset_password_user_not_found(self, password_reset_service, mock_db):
        """Test password reset when user not found"""
        token = TokenGenerator.generate_token()
        token_hash = TokenGenerator.hash_token(token)
        
        mock_reset_token = Mock(spec=PasswordResetToken)
        mock_reset_token.token = token_hash
        mock_reset_token.user_id = 999
        mock_reset_token.is_valid.return_value = True
        
        mock_password_hasher = Mock()
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_reset_token, None]
        
        result = password_reset_service.reset_password(token, 'NewPassword123!', mock_password_hasher)
        
        assert result['success'] is False
        assert 'An error occurred' in result['message']
    
    def test_is_rate_limited_no_previous_attempt(self, password_reset_service, mock_user):
        """Test rate limiting when no previous attempts"""
        mock_user.password_reset_last_attempt = None
        
        result = password_reset_service._is_rate_limited(mock_user)
        
        assert result is False
    
    def test_is_rate_limited_within_window(self, password_reset_service, mock_user):
        """Test rate limiting within time window"""
        mock_user.password_reset_attempts = 5
        mock_user.password_reset_last_attempt = datetime.utcnow() - timedelta(minutes=30)
        
        result = password_reset_service._is_rate_limited(mock_user)
        
        assert result is True
    
    def test_is_rate_limited_outside_window(self, password_reset_service, mock_user):
        """Test rate limiting outside time window"""
        mock_user.password_reset_attempts = 5
        mock_user.password_reset_last_attempt = datetime.utcnow() - timedelta(hours=2)
        
        result = password_reset_service._is_rate_limited(mock_user)
        
        assert result is False