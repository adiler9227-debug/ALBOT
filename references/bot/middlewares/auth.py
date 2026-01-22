"""Auth middleware."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services import add_user, user_exists


class AuthMiddleware(BaseMiddleware):
    """Middleware to add new users to database."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Add user to database if not exists.

        Args:
            handler: Handler function
            event: Telegram event
            data: Handler data

        Returns:
            Handler result
        """
        user: User | None = data.get("event_from_user")
        session: AsyncSession | None = data.get("session")

        if user and session:
            if not await user_exists(session, user.id):
                # Parse referrer from command argument if available
                referrer = None
                # You can parse referrer from start command here if needed

                await add_user(session, user, referrer)
                logger.info(f"✅ New user added via middleware: {user.id} (@{user.username})")

        return await handler(event, data)
