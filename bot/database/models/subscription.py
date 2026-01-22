"""Subscription model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .user import UserModel


class SubscriptionModel(Base):
    """User subscription model."""

    __tablename__ = "subscriptions"
    __table_args__ = {"comment": "User subscriptions"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    expires_at: Mapped[datetime.datetime]
    tariff_days: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[created_at]

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="subscription")

    repr_cols = ("id", "user_id", "expires_at", "is_active")
