"""Referral system models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .user import UserModel


class ReferralModel(Base):
    """Referral tracking model."""

    __tablename__ = "referrals"
    __table_args__ = {"comment": "Referral program tracking"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    referred_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_bonus_given: Mapped[bool] = mapped_column(default=False)
    bonus_given_at: Mapped[created_at | None] = mapped_column(default=None)
    created_at: Mapped[created_at]

    # Relationships
    referrer: Mapped[UserModel] = relationship(
        "UserModel", foreign_keys=[referrer_id], back_populates="referrals_made"
    )
    referred: Mapped[UserModel] = relationship(
        "UserModel", foreign_keys=[referred_id], back_populates="referred_by"
    )

    repr_cols = ("id", "referrer_id", "referred_id", "is_bonus_given")
