"""User model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base, big_int_pk, created_at

if TYPE_CHECKING:
    from .subscription import SubscriptionModel
    from .payment import PaymentModel
    from .agreement import AgreementModel
    from .lesson_progress import LessonProgressModel


class UserModel(Base):
    """User model."""

    __tablename__ = "users"
    __table_args__ = {"comment": "Telegram users"}

    id: Mapped[big_int_pk]
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(10))
    referrer: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[created_at]

    is_admin: Mapped[bool] = mapped_column(default=False)
    is_premium: Mapped[bool] = mapped_column(default=False)

    # Relationships
    subscription: Mapped[SubscriptionModel | None] = relationship(
        "SubscriptionModel", back_populates="user", uselist=False
    )
    payments: Mapped[list[PaymentModel]] = relationship("PaymentModel", back_populates="user")
    agreement: Mapped[AgreementModel | None] = relationship("AgreementModel", back_populates="user", uselist=False)
    lesson_progress: Mapped[LessonProgressModel | None] = relationship(
        "LessonProgressModel", back_populates="user", uselist=False
    )

    repr_cols = ("id", "first_name", "username")
