"""
Flowra application configuration.

All settings are loaded from environment variables (or a .env file).
Pydantic Settings validates types and raises clear errors at startup —
there are no runtime surprises from missing environment variables.

Usage:
    from app.core.config import settings
    settings.DATABASE_URL
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Master settings for the Flowra platform."""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "Flowra API"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development")         # development | staging | production
    DEBUG: bool = Field(default=True)
    PORT: int = Field(default=8000)

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = Field(default="CHANGE_ME_in_production_min_32_chars_long")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    # ------------------------------------------------------------------
    # Database (PostgreSQL via psycopg2)
    # ------------------------------------------------------------------
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "flowra"
    DB_PASSWORD: str = "flowra_local"
    DB_NAME: str = "flowra_db"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # WhatsApp Business Cloud API
    # ------------------------------------------------------------------
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v18.0"

    # ------------------------------------------------------------------
    # Gmail / Google OAuth2
    # ------------------------------------------------------------------
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/gmail/callback"
    GOOGLE_CALENDAR_REDIRECT_URI: str = "http://localhost:8000/api/v1/calendar/callback"
    OAUTH_ENCRYPTION_KEY: Optional[str] = None   # Fernet key for token encryption

    # ------------------------------------------------------------------
    # Razorpay
    # ------------------------------------------------------------------
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    OPENAI_API_KEY: Optional[str] = None

    # ------------------------------------------------------------------
    # Slack
    # ------------------------------------------------------------------
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None

    # ------------------------------------------------------------------
    # Notion
    # ------------------------------------------------------------------
    NOTION_API_KEY: Optional[str] = None

    # ------------------------------------------------------------------
    # SMTP (fallback / transactional email)
    # ------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "Flowra CRM"

    # ------------------------------------------------------------------
    # Cloudflare R2 (file storage)
    # ------------------------------------------------------------------
    CLOUDFLARE_R2_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_R2_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_R2_SECRET_KEY: Optional[str] = None
    CLOUDFLARE_R2_BUCKET_NAME: str = "flowra-uploads"

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    ENABLE_AUTOMATION: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_WHATSAPP: bool = True
    ENABLE_GMAIL: bool = True
    ENABLE_BILLING: bool = True

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False    # True in production for structured JSON logs

    # ------------------------------------------------------------------
    # Pydantic Settings
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def database_url(self) -> str:
        """
        Build the psycopg2 sync database URL.

        Priority order:
          1. DATABASE_URL env var   (Docker / production)
          2. Individual DB_* vars   (local development)
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Normalise to psycopg2 driver if plain postgresql:// is given
            if url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def is_dev(self) -> bool:
        return self.ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.ENV == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENV == "staging"

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters.")
        return v

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}, got '{v}'.")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


settings: Settings = get_settings()
