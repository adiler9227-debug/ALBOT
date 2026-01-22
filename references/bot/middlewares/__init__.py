"""Middlewares package."""

from __future__ import annotations

from aiogram import Dispatcher

from .auth import AuthMiddleware
from .database import DatabaseMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    """
    Register all middlewares.

    Args:
        dp: Dispatcher instance
    """
    # Register database middleware first (so session is available in other middlewares)
    dp.update.middleware(DatabaseMiddleware())

    # Register auth middleware (depends on database session)
    dp.update.middleware(AuthMiddleware())


__all__ = [
    "DatabaseMiddleware",
    "AuthMiddleware",
    "register_middlewares",
]
