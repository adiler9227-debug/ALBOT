"""Menu handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    main_keyboard, 
    agreement_keyboard, 
    back_to_main_keyboard,
    documents_keyboard
)
from bot.services import check_agreement

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def main_menu_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show main menu.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    logger.info(f"🔘 User {callback.from_user.id} requested main menu")

    # Check agreement
    if not await check_agreement(session, callback.from_user.id):
        logger.warning(f"⛔ User {callback.from_user.id} tried to access menu without agreement")
        agreement_text = (
            f"👋 Привет, {callback.from_user.first_name}!\n\n"
            "Чтобы продолжить, ознакомьтесь с документами и примите условия использования.\n\n"
            "Нажмите на кнопки ниже 👇"
        )
        await callback.message.edit_text(
            text=agreement_text,
            reply_markup=agreement_keyboard(),
        )
        await callback.answer("Требуется согласие")
        return

    menu_text = (
        f"🏠 Главное меню\n\n"
        f"Рад видеть тебя, {callback.from_user.first_name}! 👋\n\n"
        "Выберите интересующий раздел ниже:"
    )

    try:
        await callback.message.edit_text(
            text=menu_text,
            reply_markup=main_keyboard(),
        )
    except Exception:
        # Ignore errors if message not modified
        pass
    
    await callback.answer()


@router.callback_query(F.data == "menu:documents")
async def documents_handler(callback: CallbackQuery) -> None:
    """
    Show documents menu.

    Args:
        callback: Callback query
    """
    logger.info(f"🔘 User {callback.from_user.id} requested documents")

    documents_text = (
        "📄 Документы\n\n"
        "Здесь вы можете ознакомиться с документами:\n\n"
        "1. Публичная оферта — условия оказания услуг\n"
        "2. Политика конфиденциальности — как мы храним данные\n"
        "3. Согласие на рассылку — условия получения сообщений"
    )

    try:
        await callback.message.edit_text(
            text=documents_text,
            reply_markup=documents_keyboard(),
        )
    except TelegramBadRequest:
        # Ignore if message is not modified
        pass
        
    await callback.answer()


@router.callback_query(F.data == "menu:info")
async def info_handler(callback: CallbackQuery) -> None:
    """
    Show info.

    Args:
        callback: Callback query
    """
    info_text = (
        "ℹ️ О боте\n\n"
        "Этот бот — твой проводник в мир дыхательных практик и Кундалини йоги.\n\n"
        "Автор: Алина Баженова\n"
        "Опыт: 6+ лет\n\n"
        "Что ты получишь:\n"
        "• Дыхательные практики\n"
        "• Занятия по Кундалини йоге\n"
        "• Техники работы с тревожностью и стрессом\n"
        "• Улучшение сна и самочувствия\n"
        "• Повышение энергии и уверенности\n\n"
        "<a href='https://t.me/breathBaniJaipreet/928'>Посмотреть, как устроен клуб (ссылка на отзывы участников и видео, как всё выглядит внутри)</a>\n\n"
        "Присоединяйся! 🌿"
    )

    try:
        await callback.message.edit_text(
            text=info_text,
            reply_markup=back_to_main_keyboard(),
        )
    except Exception:
        pass
        
    await callback.answer()
