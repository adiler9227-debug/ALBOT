"""Bot configuration."""

from __future__ import annotations

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvBaseSettings(BaseSettings):
    """Base settings with .env file support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class BotSettings(EnvBaseSettings):
    """Bot settings."""

    BOT_TOKEN: str
    SUPPORT_URL: str | None = None
    RATE_LIMIT: int | float = 0.5
    DEBUG: bool = False
    USE_WEBHOOK: bool = False
    WEBHOOK_BASE_URL: str | None = None
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_SECRET: str | None = None
    WEBHOOK_HOST: str = "0.0.0.0"
    WEBHOOK_PORT: int = 8080


class DBSettings(EnvBaseSettings):
    """Database settings."""

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "bot_db"

    @property
    def database_url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class CacheSettings(EnvBaseSettings):
    """Redis cache settings."""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASS: str | None = None
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        password = f":{self.REDIS_PASS}@" if self.REDIS_PASS else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class PaymentSettings(EnvBaseSettings):
    """Payment and subscription settings."""

    PAYMENT_TOKEN: str
    CHANNEL_ID: int
    OFFER_DOCUMENT_URL: str = "https://example.com/offer.pdf"
    PRIVACY_DOCUMENT_URL: str = "https://example.com/privacy.pdf"
    CONSENT_DOCUMENT_URL: str = "https://example.com/consent.pdf"

    # Tariffs configuration
    TARIFF_30_DAYS: int = 30
    TARIFF_30_PRICE: int = 199000  # 1990 RUB in kopecks
    TARIFF_90_DAYS: int = 90
    TARIFF_90_PRICE: int = 477000  # 4770 RUB in kopecks
    TARIFF_365_DAYS: int = 365
    TARIFF_365_PRICE: int = 1590000  # 15900 RUB in kopecks

    # Reminder settings
    REMINDER_DELAY_SECONDS: int = 600  # 10 minutes
    SAD_CAT_PHOTO_URL: str = "https://i.imgur.com/sad_cat.jpg"


class AnalyticsSettings(EnvBaseSettings):
    """Analytics settings."""

    SENTRY_DSN: str | None = None
    AMPLITUDE_API_KEY: str | None = None
    POSTHOG_API_KEY: str | None = None


class Settings:
    """Application settings."""

    def __init__(self) -> None:
        self.bot = BotSettings()
        self.db = DBSettings()
        self.cache = CacheSettings()
        self.payment = PaymentSettings()
        self.analytics = AnalyticsSettings()


# Singleton instance
settings = Settings()
