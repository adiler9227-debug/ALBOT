"""Bot configuration."""

from __future__ import annotations

import os

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvBaseSettings(BaseSettings):
    """Base settings with .env file support (optional)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_file_optional=True,  # .env file is optional
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
    WEBHOOK_PORT: int = int(os.getenv("PORT", "8080"))


class DBSettings(EnvBaseSettings):
    """Database settings."""

    # Railway provides DATABASE_URL, parse it if available
    DATABASE_URL: str | None = None

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "bot_db"

    @property
    def database_url(self) -> str:
        """Get database URL."""
        # Use Railway's DATABASE_URL if available
        if self.DATABASE_URL:
            # Replace postgres:// with postgresql+asyncpg://
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace(
                "postgres://", "postgresql+asyncpg://"
            )

        # Otherwise construct from individual params
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class CacheSettings(EnvBaseSettings):
    """Redis cache settings."""

    # Railway provides REDIS_URL
    REDIS_URL: str | None = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASS: str | None = None
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        # Use Railway's REDIS_URL if available
        if self.REDIS_URL:
            return self.REDIS_URL

        # Otherwise construct from individual params
        password = f":{self.REDIS_PASS}@" if self.REDIS_PASS else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class PaymentSettings(EnvBaseSettings):
    """Payment and subscription settings."""

    # Telegram Payments
    PAYMENT_TOKEN: str | None = None

    # Prodamus settings
    PRODAMUS_DOMAIN: str = "club-breathing.payform.ru"
    PRODAMUS_SECRET_KEY: str = Field(alias="PRODAMUS_SECRET_KEY")

    # Channel settings
    CHANNEL_ID: int = -3394467411

    # Documents
    OFFER_DOCUMENT_URL: str = "https://telegra.ph/Dogovor-oferty-Klub-Dyhaniya-01-18"
    PRIVACY_DOCUMENT_URL: str = "https://telegra.ph/Politika-konfidencialnosti-Klub-Dyhaniya-01-18"
    CONSENT_DOCUMENT_URL: str = "https://telegra.ph/Soglasie-na-obrabotku-dannyh-Klub-Dyhaniya-01-18"

    # Tariffs configuration (prices in rubles)
    TARIFF_7_DAYS: int = 7
    TARIFF_7_PRICE: int = 490

    TARIFF_30_DAYS: int = 30
    TARIFF_30_PRICE: int = 1990

    TARIFF_90_DAYS: int = 90
    TARIFF_90_PRICE: int = 4990

    TARIFF_180_DAYS: int = 180
    TARIFF_180_PRICE: int = 8990

    TARIFF_365_DAYS: int = 365
    TARIFF_365_PRICE: int = 16490

    # Promocodes
    VIDEO_REVIEW_PROMO: str = "VIDEOOTZIV"
    VIDEO_REVIEW_DISCOUNT: int = 1000  # 1000 RUB discount

    # Referral program
    REFERRAL_BONUS_DAYS: int = 30  # +1 month for referrer

    # Reminder settings
    REMINDER_DELAY_SECONDS: int = 600  # 10 minutes
    REMINDER_48H_SECONDS: int = 172800  # 48 hours
    REMINDER_BEFORE_EXPIRY_DAYS: int = 3  # 3 days before expiry

    SAD_CAT_PHOTO_URL: str = "https://i.imgur.com/sad_cat.jpg"
    LESSON_VIDEO_URL: str | None = None  # URL or File ID of the lesson video
    PRACTICE_VIDEO_FILE_ID: str = "BAACAgIAAxkBAAEalcJpgD-JF9p0GmWeeVhNE0PwVqpBewAC_pYAAnQN8EvVT93rZTtAhTgE"


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
