"""Promocode model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .user import UserModel


class PromocodeModel(Base):
    """Promocode model."""

    __tablename__ = "promocodes"
    __table_args__ = {"comment": "Promocodes"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_amount: Mapped[int]  # Discount in rubles
    is_active: Mapped[bool] = mapped_column(default=True)
    max_uses: Mapped[int | None]  # None = unlimited
    current_uses: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[created_at]

    repr_cols = ("id", "code", "discount_amount", "is_active")


class PromocodeUsageModel(Base):
    """Promocode usage tracking."""

    __tablename__ = "promocode_usage"
    __table_args__ = {"comment": "Promocode usage history"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    promocode_id: Mapped[int] = mapped_column(ForeignKey("promocodes.id", ondelete="CASCADE"))
    used_at: Mapped[created_at]

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel")
    promocode: Mapped[PromocodeModel] = relationship("PromocodeModel")

    repr_cols = ("id", "user_id", "promocode_id")
