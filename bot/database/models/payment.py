"""Payment model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import UserModel


class PaymentModel(Base):
    """Payment model."""

    __tablename__ = "payments"
    __table_args__ = {"comment": "User payments"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[int]  # Amount in kopecks/cents
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    tariff_days: Mapped[int]
    payment_date: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="payments")

    repr_cols = ("id", "user_id", "amount", "payment_date")
