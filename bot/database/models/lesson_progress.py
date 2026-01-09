"""Lesson progress model."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import UserModel


class LessonProgressModel(Base):
    """Lesson progress model."""

    __tablename__ = "lesson_progress"
    __table_args__ = {"comment": "User lesson progress"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_lesson_started_at: Mapped[datetime.datetime | None]
    lesson_clicked: Mapped[bool] = mapped_column(default=False)
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped[UserModel] = relationship("UserModel", back_populates="lesson_progress")

    repr_cols = ("id", "user_id", "lesson_clicked", "reminder_sent")
