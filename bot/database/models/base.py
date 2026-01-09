"""Base models and type annotations."""

from __future__ import annotations

import datetime
from typing import Annotated

from sqlalchemy import BigInteger, text
from sqlalchemy.orm import DeclarativeBase, mapped_column


int_pk = Annotated[int, mapped_column(primary_key=True, unique=True, autoincrement=False)]
big_int_pk = Annotated[int, mapped_column(primary_key=True, unique=True, autoincrement=False, type_=BigInteger)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


class Base(DeclarativeBase):
    """Base class for all models."""

    repr_cols_num = 3
    repr_cols: tuple[str, ...] = ()

    def __repr__(self) -> str:
        """Return string representation of model."""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"
