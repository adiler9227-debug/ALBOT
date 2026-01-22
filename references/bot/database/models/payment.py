"""Payment model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .user import UserModel


class PaymentModel(Base):
    """Payment model."""

    __tablename__ = "payments"
    __table_args__ = {"comment": "Payment transactions"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int]  # Amount in rubles (not kopecks)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    subscription_days: Mapped[int]
    payment_provider: Mapped[str] = mapped_column(String(50), default="prodamus")
    payment_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[created_at]

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="payments")

    repr_cols = ("id", "user_id", "amount", "status", "created_at")
