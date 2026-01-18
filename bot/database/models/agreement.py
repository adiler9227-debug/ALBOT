"""Agreement model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .user import UserModel


class AgreementModel(Base):
    """User agreement model."""

    __tablename__ = "agreements"
    __table_args__ = {"comment": "User agreements with terms"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    agreed_to_offer: Mapped[bool] = mapped_column(default=False)
    agreed_to_privacy: Mapped[bool] = mapped_column(default=False)
    agreed_to_consent: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[created_at]
    updated_at: Mapped[created_at]

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="agreement")

    repr_cols = ("id", "user_id", "agreed_to_offer")
