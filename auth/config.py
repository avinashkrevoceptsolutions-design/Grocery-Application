import os
from dotenv import load_dotenv

load_dotenv()

# Password reset configuration
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 24))
PASSWORD_RESET_MAX_REQUESTS = int(os.getenv('PASSWORD_RESET_MAX_REQUESTS', 5))
PASSWORD_RESET_RATE_LIMIT_WINDOW = int(os.getenv('PASSWORD_RESET_RATE_LIMIT_WINDOW', 3600))

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'noreply@example.com')

# Frontend configuration
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')

# Security
CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'True').lower() == 'true'
CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', 'your-secret-key-change-in-production')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'auth.log')