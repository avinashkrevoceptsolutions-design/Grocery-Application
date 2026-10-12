from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    
    # Indexes for query optimization
    __table_args__ = (
        Index('idx_user_id_expires_at', 'user_id', 'expires_at'),
        Index('idx_token_expires_at', 'token', 'expires_at'),
    )
    
    user = relationship('User', back_populates='password_reset_tokens')
    
    def is_valid(self) -> bool:
        """Check if token is still valid (not expired and not used)"""
        return not self.is_used and self.expires_at > datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if token has expired"""
        return self.expires_at <= datetime.utcnow()