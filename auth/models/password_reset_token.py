from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    is_used = Column(String(1), default='0')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token}>'
    
    def is_valid(self):
        return not self.is_used and datetime.utcnow() < self.expires_at
