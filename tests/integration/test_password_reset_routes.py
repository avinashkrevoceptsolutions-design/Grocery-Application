import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock
from src.main import app
from src.models.user import User
from src.models.password_reset_token import PasswordResetToken
from datetime import datetime, timedelta


client = TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock(spec=Session)


class TestPasswordResetRoutes:
    """Test cases for password reset routes."""

    @pytest.mark.asyncio
    async def test_forgot_password_success(self):
        """Test successful forgot password request."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.generate_reset_token = AsyncMock(return_value=(True, "If an account exists", "token123"))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/forgot-password",
                json={"email": "test@example.com"}
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_forgot_password_rate_limit(self):
        """Test forgot password with rate limit exceeded."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.generate_reset_token = AsyncMock(return_value=(False, "Too many requests", None))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/forgot-password",
                json={"email": "test@example.com"}
            )
            
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test successful password reset."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.reset_password = AsyncMock(return_value=(True, "Password reset successfully"))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/reset-password",
                json={
                    "token": "abc123def456ghi789jkl012mno345pqr",
                    "new_password": "NewPassword123",
                    "confirm_password": "NewPassword123"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_reset_password_mismatch(self):
        """Test password reset with mismatched passwords."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            response = client.post(
                "/auth/reset-password",
                json={
                    "token": "abc123def456ghi789jkl012mno345pqr",
                    "new_password": "NewPassword123",
                    "confirm_password": "DifferentPassword123"
                }
            )
            
            assert response.status_code == 400
            assert "do not match" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self):
        """Test password reset with invalid token."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.reset_password = AsyncMock(return_value=(False, "Invalid token"))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/reset-password",
                json={
                    "token": "invalid-token",
                    "new_password": "NewPassword123",
                    "confirm_password": "NewPassword123"
                }
            )
            
            assert response.status_code == 400

    def test_validate_reset_token_valid(self):
        """Test validation of valid reset token."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.validate_reset_token = Mock(return_value=(True, "Valid", "user-123"))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/validate-reset-token",
                json={"token": "valid-token"}
            )
            
            assert response.status_code == 200
            assert response.json()["is_valid"] is True
            assert response.json()["user_id"] == "user-123"

    def test_validate_reset_token_invalid(self):
        """Test validation of invalid reset token."""
        with patch('src.routes.password_reset_routes.get_db') as mock_get_db, \
             patch('src.routes.password_reset_routes.get_email_service') as mock_get_email, \
             patch('src.routes.password_reset_routes.PasswordResetService') as mock_service_class:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_email_service = Mock()
            mock_get_email.return_value = mock_email_service
            
            mock_service = Mock()
            mock_service.validate_reset_token = Mock(return_value=(False, "Invalid token", None))
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/auth/validate-reset-token",
                json={"token": "invalid-token"}
            )
            
            assert response.status_code == 200
            assert response.json()["is_valid"] is False
