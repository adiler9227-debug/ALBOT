"""Database middleware."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from loguru import logger

from bot.database import sessionmaker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session into handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Inject database session into handler data.

        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data

        Returns:
            Handler result
        """
        async with sessionmaker() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception as e:
                logger.error(f"❌ Error in handler: {e}")
                raise
