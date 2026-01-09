"""Handlers package."""

from __future__ import annotations

from aiogram import Router

from . import agreement, lessons, menu, payments, start, subscription


def get_handlers_router() -> Router:
    """
    Get router with all handlers.

    Returns:
        Router with all handlers
    """
    router = Router(name="main")

    # Order matters - more specific handlers should be registered first
    router.include_router(start.router)
    router.include_router(agreement.router)
    router.include_router(menu.router)
    router.include_router(lessons.router)
    router.include_router(payments.router)
    router.include_router(subscription.router)

    return router


__all__ = [
    "get_handlers_router",
]
