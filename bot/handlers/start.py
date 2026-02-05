"""Start command handler."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import agreement_keyboard, main_keyboard
from bot.keyboards.reply import main_menu
from bot.services import add_user, check_agreement, user_exists
from bot.core.config import settings

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

    # Parse referrer from deep link
    referrer_id = None
    if message.text and message.text.startswith("/start ref_"):
        try:
            referrer_id = int(message.text.split("ref_")[1])
            logger.info(f"User {user_id} came from referral link of user {referrer_id}")
        except (IndexError, ValueError):
            logger.warning(f"Invalid referral code in: {message.text}")

    # Add user if not exists
    is_new_user = False
    if not await user_exists(session, user_id):
        await add_user(session, message.from_user, referrer=None)
        is_new_user = True
        logger.info(f"New user registered: {user_id} (@{message.from_user.username})")

        # Create referral record if came from referral link
        if referrer_id and referrer_id != user_id:
            from bot.database.models import ReferralModel

            # Check if referrer exists
            if await user_exists(session, referrer_id):
                referral = ReferralModel(
                    referrer_id=referrer_id,
                    referred_id=user_id,
                )
                session.add(referral)
                await session.commit()
                logger.info(f"Created referral: {referrer_id} → {user_id}")

    # Check if user agreed to terms
    if not await check_agreement(session, user_id):
        # Show agreement screen with photo
        agreement_text = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Добро пожаловать в мир дыхательных практик и кундалини-йоги 🧘‍♀️\n\n"
            "Чтобы продолжить, ознакомьтесь с документами и примите условия использования.\n\n"
            "Нажмите на кнопки ниже 👇"
        )

        # Show agreement screen (text only)
        await message.answer(
            text=agreement_text,
            reply_markup=agreement_keyboard(),
        )
    else:
        # Show main menu
        welcome_text = (
            f"👋 С возвращением, {message.from_user.first_name}!\n\n"
            "Рада видеть тебя снова! 🌿"
        )

        # Send text with Reply keyboard
        await message.answer(
            text=welcome_text,
            reply_markup=main_menu,
        )
        
        # Send Inline keyboard
        await message.answer(
            text="🏠 Главное меню\n\nВыберите интересующий раздел ниже:",
            reply_markup=main_keyboard(),
        )
