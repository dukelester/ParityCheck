"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://paritycheck:paritycheck@localhost:5432/paritycheck"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    API_KEY_HEADER: str = "X-API-Key"
    FRONTEND_URL: str = "http://localhost:5173"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email (SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@paritycheck.io"
    SMTP_FROM_NAME: str = "ParityCheck"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    DEV_SKIP_EMAIL: bool = False  # When True, log verification links instead of sending


settings = Settings()
