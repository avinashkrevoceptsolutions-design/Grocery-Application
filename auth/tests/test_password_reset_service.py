import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from auth.services.password_reset_service import PasswordResetService
from auth.services.email_service import EmailService
from auth.models.password_reset_token import PasswordResetToken
from auth.models.user import User
from auth.utils.password_utils import hash_password


class TestPasswordResetService:
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_email_service(self):
        """Create mock email service"""
        service = Mock(spec=EmailService)
        service.send_password_reset_email.return_value = True
        return service
    
    @pytest.fixture
    def password_reset_service(self, mock_db, mock_email_service):
        """Create password reset service instance"""
        return PasswordResetService(
            db_session=mock_db,
            email_service=mock_email_service
        )
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = Mock(spec=User)
        user.id = 1
        user.email = 'test@example.com'
        user.username = 'testuser'
        user.password_hash = hash_password('oldpassword123!')
        return user
    
    def test_generate_reset_token_success(
        self,
        password_reset_service,
        mock_db,
        mock_user
    ):
        """Test successful reset token generation"""
        # Setup
        mock_db.query.return_value.filter.return_value.update.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        success, message = password_reset_service.generate_reset_token(
            user_id=mock_user.id,
            email=mock_user.email
        )
        
        # Assert
        assert success is True
        assert 'sent' in message.lower()
    
    def test_generate_reset_token_email_failure(
        self,
        password_reset_service,
        mock_db,
        mock_email_service,
        mock_user
    ):
        """Test reset token generation when email fails to send"""
        # Setup
        mock_email_service.send_password_reset_email.return_value = False
        mock_db.query.return_value.filter.return_value.update.return_value = None
        mock_db.commit.return_value = None
        
        # Execute
        success, message = password_reset_service.generate_reset_token(
            user_id=mock_user.id,
            email=mock_user.email
        )
        
        # Assert
        assert success is False
    
    def test_validate_token_success(self, password_reset_service, mock_db, mock_user):
        """Test successful token validation"""
        # Setup
        valid_token = PasswordResetToken(
            id=1,
            user_id=mock_user.id,
            token='test_token_123',
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        valid_token.is_used = False
        valid_token.is_expired = Mock(return_value=False)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            valid_token,
            mock_user
        ]
        
        # Execute
        is_valid, user_info = password_reset_service.validate_token('test_token_123')
        
        # Assert
        assert is_valid is True
        assert user_info is not None
        assert user_info['user_id'] == mock_user.id
        assert user_info['email'] == mock_user.email
    
    def test_validate_token_expired(
        self,
        password_reset_service,
        mock_db
    ):
        """Test validation of expired token"""
        # Setup
        expired_token = PasswordResetToken(
            id=1,
            user_id=1,
            token='test_token_123',
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_used=False
        )
        expired_token.is_used = False
        expired_token.is_expired = Mock(return_value=True)
        
        mock_db.query.return_value.filter.return_value.first.return_value = expired_token
        
        # Execute
        is_valid, user_info = password_reset_service.validate_token('test_token_123')
        
        # Assert
        assert is_valid is False
        assert user_info is None
    
    def test_validate_token_already_used(
        self,
        password_reset_service,
        mock_db
    ):
        """Test validation of already-used token"""
        # Setup
        used_token = PasswordResetToken(
            id=1,
            user_id=1,
            token='test_token_123',
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=True
        )
        used_token.is_expired = Mock(return_value=False)
        
        mock_db.query.return_value.filter.return_value.first.return_value = used_token
        
        # Execute
        is_valid, user_info = password_reset_service.validate_token('test_token_123')
        
        # Assert
        assert is_valid is False
        assert user_info is None
    
    def test_reset_password_success(
        self,
        password_reset_service,
        mock_db,
        mock_user
    ):
        """Test successful password reset"""
        # Setup
        valid_token = PasswordResetToken(
            id=1,
            user_id=mock_user.id,
            token='test_token_123',
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        valid_token.is_used = False
        valid_token.is_expired = Mock(return_value=False)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            valid_token,
            mock_user,
            valid_token
        ]
        mock_db.commit.return_value = None
        
        # Execute
        success, message = password_reset_service.reset_password(
            token='test_token_123',
            new_password='NewPassword123!'
        )
        
        # Assert
        assert success is True
        assert 'successful' in message.lower()
        assert mock_user.password_hash != hash_password('NewPassword123!')
    
    def test_reset_password_invalid_token(
        self,
        password_reset_service,
        mock_db
    ):
        """Test password reset with invalid token"""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        success, message = password_reset_service.reset_password(
            token='invalid_token',
            new_password='NewPassword123!'
        )
        
        # Assert
        assert success is False
    
    def test_cleanup_expired_tokens(
        self,
        password_reset_service,
        mock_db
    ):
        """Test cleanup of expired tokens"""
        # Setup
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        mock_db.commit.return_value = None
        
        # Execute
        deleted_count = password_reset_service.cleanup_expired_tokens()
        
        # Assert
        assert deleted_count == 5
        mock_db.commit.assert_called_once()