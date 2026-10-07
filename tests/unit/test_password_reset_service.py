import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from src.services.password_reset_service import PasswordResetService
from src.models.password_reset_token import PasswordResetToken
from src.models.user import User
from src.utils.email_service import MockEmailService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_email_service():
    """Create a mock email service."""
    return MockEmailService()


@pytest.fixture
def password_reset_service(mock_db, mock_email_service):
    """Create a password reset service instance."""
    return PasswordResetService(mock_db, mock_email_service)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = "user-123"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.hashed_password = "hashed_password"
    return user


class TestPasswordResetService:
    """Test cases for PasswordResetService."""

    @pytest.mark.asyncio
    async def test_generate_reset_token_success(self, password_reset_service, mock_db, mock_user):
        """Test successful token generation."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        success, message, token = await password_reset_service.generate_reset_token("test@example.com")

        assert success is True
        assert token is not None
        assert len(token) >= 32
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_generate_reset_token_user_not_found(self, password_reset_service, mock_db):
        """Test token generation for non-existent user."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        success, message, token = await password_reset_service.generate_reset_token("nonexistent@example.com")

        assert success is True
        assert token is None
        assert "If an account exists" in message

    @pytest.mark.asyncio
    async def test_generate_reset_token_rate_limit_exceeded(self, password_reset_service, mock_db, mock_user):
        """Test rate limiting for token generation."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        success, message, token = await password_reset_service.generate_reset_token("test@example.com")

        assert success is False
        assert token is None
        assert "Too many" in message

    def test_validate_reset_token_valid(self, password_reset_service, mock_db):
        """Test validation of a valid token."""
        mock_token = Mock(spec=PasswordResetToken)
        mock_token.is_used = False
        mock_token.is_expired.return_value = False
        mock_token.user_id = "user-123"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_token

        is_valid, message, user_id = password_reset_service.validate_reset_token("valid-token")

        assert is_valid is True
        assert user_id == "user-123"
        assert "valid" in message.lower()

    def test_validate_reset_token_not_found(self, password_reset_service, mock_db):
        """Test validation of non-existent token."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        is_valid, message, user_id = password_reset_service.validate_reset_token("invalid-token")

        assert is_valid is False
        assert user_id is None
        assert "Invalid" in message

    def test_validate_reset_token_already_used(self, password_reset_service, mock_db):
        """Test validation of already used token."""
        mock_token = Mock(spec=PasswordResetToken)
        mock_token.is_used = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_token

        is_valid, message, user_id = password_reset_service.validate_reset_token("used-token")

        assert is_valid is False
        assert user_id is None
        assert "already been used" in message

    def test_validate_reset_token_expired(self, password_reset_service, mock_db):
        """Test validation of expired token."""
        mock_token = Mock(spec=PasswordResetToken)
        mock_token.is_used = False
        mock_token.is_expired.return_value = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_token

        is_valid, message, user_id = password_reset_service.validate_reset_token("expired-token")

        assert is_valid is False
        assert user_id is None
        assert "expired" in message.lower()

    @pytest.mark.asyncio
    async def test_reset_password_success(self, password_reset_service, mock_db, mock_user):
        """Test successful password reset."""
        mock_token = Mock(spec=PasswordResetToken)
        mock_token.is_used = False
        mock_token.is_expired.return_value = False
        mock_token.user_id = "user-123"
        mock_token.mark_as_used = Mock()

        # Setup mock for validate_reset_token
        with patch.object(password_reset_service, 'validate_reset_token', return_value=(True, "Valid", "user-123")):
            # Setup mock for user query
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            success, message = await password_reset_service.reset_password("valid-token", "NewPassword123")

            assert success is True
            assert "successfully" in message.lower()
            assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, password_reset_service, mock_db):
        """Test password reset with invalid token."""
        with patch.object(password_reset_service, 'validate_reset_token', return_value=(False, "Invalid token", None)):
            success, message = await password_reset_service.reset_password("invalid-token", "NewPassword123")

            assert success is False
            assert "Invalid" in message

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, password_reset_service, mock_db):
        """Test password reset with weak password."""
        with patch.object(password_reset_service, 'validate_reset_token', return_value=(True, "Valid", "user-123")):
            success, message = await password_reset_service.reset_password("valid-token", "weak")

            assert success is False
            assert "security requirements" in message.lower()

    def test_cleanup_expired_tokens(self, password_reset_service, mock_db):
        """Test cleanup of expired tokens."""
        mock_db.query.return_value.filter.return_value.delete.return_value = 5

        deleted_count = password_reset_service.cleanup_expired_tokens()

        assert deleted_count == 5
        assert mock_db.commit.called

    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password."""
        assert PasswordResetService._validate_password_strength("ValidPassword123") is True

    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password."""
        assert PasswordResetService._validate_password_strength("Short1") is False

    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase."""
        assert PasswordResetService._validate_password_strength("lowercase123") is False

    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase."""
        assert PasswordResetService._validate_password_strength("UPPERCASE123") is False

    def test_validate_password_strength_no_numbers(self):
        """Test password strength validation without numbers."""
        assert PasswordResetService._validate_password_strength("NoNumbers") is False
