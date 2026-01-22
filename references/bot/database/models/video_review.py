"""Video review models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at

if TYPE_CHECKING:
    from .promocode import PromocodeModel
    from .user import UserModel


class VideoReviewModel(Base):
    """Video review tracking model."""

    __tablename__ = "video_reviews"
    __table_args__ = {"comment": "Video reviews from users"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    video_file_id: Mapped[str] = mapped_column(String(255))
    promocode_id: Mapped[int | None] = mapped_column(
        ForeignKey("promocodes.id", ondelete="SET NULL"), default=None
    )
    is_approved: Mapped[bool] = mapped_column(default=True)  # Auto-approve by default
    created_at: Mapped[created_at]

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="video_reviews")
    promocode: Mapped[PromocodeModel | None] = relationship("PromocodeModel")

    repr_cols = ("id", "user_id", "is_approved")
