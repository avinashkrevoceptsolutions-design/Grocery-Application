from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from auth.database import Base


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='password_reset_tokens')

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired() and not self.is_used

    __table_args__ = (
        Index('idx_user_id_expires_at', 'user_id', 'expires_at'),
        Index('idx_token_expires_at', 'token', 'expires_at'),
    )
