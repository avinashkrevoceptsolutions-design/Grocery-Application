import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Grocery E-Commerce API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB Settings
    MONGO_URL: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string"
    )
    DB_NAME: str = Field(
        default="grocery_ecommerce",
        description="MongoDB database name"
    )

    # Qdrant inventory RAG settings
    QDRANT_URL: Optional[str] = Field(
        default=None,
        description="Qdrant server URL, for example http://localhost:6333"
    )
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "inventory"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    # LOW_STOCK_THRESHOLD: int = Field(default=10, ge=1)

    # Groq settings
    GROK_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "qwen/qwen3.6-27b"

    # # Optional xAI settings
    # XAI_API_KEY: Optional[str] = None
    # XAI_BASE_URL: str = "https://api.x.ai/v1"
    # XAI_MODEL: str = "grok-3-mini"
    
 
    JWT_SECRET_KEY: str = Field(
        default="grocery_ecommerce_secret_key_2026_super_secure_jwt_token",
        description="Secret key for JWT signature"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  
    
   
    ADMIN_EMAIL: str = "admin@grocery.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PHONE: str = "+19876543210"
    ADMIN_PASSWORD: str = "Admin@12345"
    ADMIN_FIRST_NAME: str = "System"
    ADMIN_LAST_NAME: str = "Administrator"


    ADMIN_EMAIL: str = "tilebi4801@koboywin.com"
    ADMIN_USERNAME: str = "admin01"
    ADMIN_PHONE: str = "+19876543219"
    ADMIN_PASSWORD: str = "Admin@123456"
    ADMIN_FIRST_NAME: str = "System"
    ADMIN_LAST_NAME: str = "Administrator"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = ""

    @property
    def clean_mongo_url(self) -> str:
        """Sanitizes Mongo URL in case of placeholder brackets < >."""
        url = self.MONGO_URL.strip()
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1]
        url = url.replace("<", "").replace(">", "")
        return url


settings = Settings()
