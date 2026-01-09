"""Start command handler."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import agreement_keyboard, main_keyboard
from bot.services import add_user, check_agreement, user_exists

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession) -> None:
    """
    Handle /start command.

    Args:
        message: Message
        session: Database session
    """
    if not message.from_user:
        return

    user_id = message.from_user.id

    # Add user if not exists
    if not await user_exists(session, user_id):
        # TODO: Parse referrer from start argument
        await add_user(session, message.from_user, referrer=None)
        logger.info(f"New user registered: {user_id} (@{message.from_user.username})")

    # Check if user agreed to terms
    if not await check_agreement(session, user_id):
        # Show agreement screen
        agreement_text = _(
            "👋 Hello, {name}!\n\n"
            "Welcome to our bot! 🎓\n\n"
            "To continue, you need to review the documents and accept the terms of use.\n\n"
            "By continuing to use the bot, you agree to:\n"
            "• Privacy Policy\n"
            "• Consent to receive promotional mailings\n"
            "• Consent to personal data processing\n\n"
            "Click the buttons below to review the documents 👇"
        ).format(name=message.from_user.first_name)

        await message.answer(
            text=agreement_text,
            reply_markup=agreement_keyboard(),
        )
    else:
        # Show main menu
        welcome_text = _(
            "👋 Welcome back, {name}!\n\n"
            "I'm happy to see you again! 🌿"
        ).format(name=message.from_user.first_name)

        await message.answer(
            text=welcome_text,
            reply_markup=main_keyboard(),
        )
