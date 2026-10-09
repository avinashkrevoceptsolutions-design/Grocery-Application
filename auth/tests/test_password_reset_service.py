import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from auth.models.password_reset_token import PasswordResetToken
from auth.models.user import User
from auth.services.password_reset_service import PasswordResetService
from auth.utils.token_generator import TokenGenerator


class TestTokenGenerator:
    """Tests for TokenGenerator utility."""

    def test_generate_token(self):
        """Test token generation."""
        token = TokenGenerator.generate_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_generate_token_uniqueness(self):
        """Test that generated tokens are unique."""
        token1 = TokenGenerator.generate_token()
        token2 = TokenGenerator.generate_token()
        assert token1 != token2

    def test_generate_token_with_expiration(self):
        """Test token generation with expiration."""
        token, expires_at = TokenGenerator.generate_token_with_expiration()
        assert token is not None
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.utcnow()

    def test_validate_token_format_valid(self):
        """Test token format validation with valid token."""
        token = TokenGenerator.generate_token()
        assert TokenGenerator.validate_token_format(token) is True

    def test_validate_token_format_invalid(self):
        """Test token format validation with invalid tokens."""
        assert TokenGenerator.validate_token_format(None) is False
        assert TokenGenerator.validate_token_format("") is False
        assert TokenGenerator.validate_token_format("short") is False
        assert TokenGenerator.validate_token_format(123) is False


class TestPasswordResetToken:
    """Tests for PasswordResetToken model."""

    def test_token_is_expired(self):
        """Test token expiration check."""
        expired_token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert expired_token.is_expired() is True

    def test_token_is_not_expired(self):
        """Test token that is not expired."""
        valid_token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert valid_token.is_expired() is False

    def test_token_is_valid(self):
        """Test token validity check."""
        valid_token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        assert valid_token.is_valid() is True

    def test_token_is_invalid_when_expired(self):
        """Test token validity when expired."""
        expired_token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_used=False
        )
        assert expired_token.is_valid() is False

    def test_token_is_invalid_when_used(self):
        """Test token validity when already used."""
        used_token = PasswordResetToken(
            user_id=1,
            token="test_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=True
        )
        assert used_token.is_valid() is False


class TestPasswordResetService:
    """Tests for PasswordResetService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        return user

    def test_generate_reset_token_success(self, mock_db, mock_user):
        """Test successful token generation."""
        token = PasswordResetService.generate_reset_token(mock_db, mock_user.id)
        
        assert token is not None
        assert isinstance(token, str)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_generate_reset_token_failure(self, mock_db):
        """Test token generation failure."""
        mock_db.commit.side_effect = Exception("Database error")
        
        token = PasswordResetService.generate_reset_token(mock_db, 1)
        
        assert token is None
        mock_db.rollback.assert_called_once()

    def test_validate_token_success(self, mock_db, mock_user):
        """Test successful token validation."""
        reset_token = PasswordResetToken(
            user_id=mock_user.id,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            reset_token,
            mock_user
        ]
        
        is_valid, user_id, email = PasswordResetService.validate_token(mock_db, "valid_token")
        
        assert is_valid is True
        assert user_id == mock_user.id
        assert email == mock_user.email

    def test_validate_token_expired(self, mock_db):
        """Test validation of expired token."""
        expired_token = PasswordResetToken(
            user_id=1,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            is_used=False
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = expired_token
        
        is_valid, user_id, email = PasswordResetService.validate_token(mock_db, "expired_token")
        
        assert is_valid is False
        assert user_id is None

    def test_validate_token_not_found(self, mock_db):
        """Test validation of non-existent token."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        is_valid, user_id, email = PasswordResetService.validate_token(mock_db, "invalid_token")
        
        assert is_valid is False
        assert user_id is None

    def test_validate_token_invalid_format(self, mock_db):
        """Test validation of invalid token format."""
        is_valid, user_id, email = PasswordResetService.validate_token(mock_db, "short")
        
        assert is_valid is False
        assert user_id is None
        mock_db.query.assert_not_called()

    @patch('auth.services.password_reset_service.EmailService')
    def test_reset_password_success(self, mock_email_service, mock_db, mock_user):
        """Test successful password reset."""
        reset_token = PasswordResetToken(
            user_id=mock_user.id,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_used=False
        )
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            reset_token,
            mock_user,
            reset_token
        ]
        
        success, message = PasswordResetService.reset_password(
            mock_db,
            "valid_token",
            "NewPassword123!"
        )
        
        assert success is True
        assert "successfully" in message.lower()
        mock_db.commit.assert_called_once()

    def test_reset_password_invalid_token(self, mock_db):
        """Test password reset with invalid token."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        success, message = PasswordResetService.reset_password(
            mock_db,
            "invalid_token",
            "NewPassword123!"
        )
        
        assert success is False
        assert "invalid" in message.lower() or "expired" in message.lower()

    @patch('auth.services.password_reset_service.EmailService')
    def test_initiate_password_reset_success(self, mock_email_service, mock_db, mock_user):
        """Test successful password reset initiation."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        success, message = PasswordResetService.initiate_password_reset(
            mock_db,
            mock_user.email
        )
        
        assert success is True
        mock_email_service.send_password_reset_email.assert_called_once()

    def test_initiate_password_reset_user_not_found(self, mock_db):
        """Test password reset initiation for non-existent user."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        success, message = PasswordResetService.initiate_password_reset(
            mock_db,
            "nonexistent@example.com"
        )
        
        # Should return success to prevent user enumeration
        assert success is True
        assert "account" in message.lower()

    def test_cleanup_expired_tokens(self, mock_db):
        """Test cleanup of expired tokens."""
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        deleted_count = PasswordResetService.cleanup_expired_tokens(mock_db)
        
        assert deleted_count == 5
        mock_db.commit.assert_called_once()
