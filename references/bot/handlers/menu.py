"""Menu handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.keyboards.inline import main_keyboard, back_to_main_keyboard

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def main_menu_handler(callback: CallbackQuery) -> None:
    """
    Show main menu.

    Args:
        callback: Callback query
    """
    logger.info(f"🔘 Callback: {callback.data} | User: {callback.from_user.id if callback.from_user else 'unknown'}")
    menu_text = (
        "🏠 Главное меню\n\n"
        "Выберите действие:"
    )

    await callback.message.edit_text(
        text=menu_text,
        reply_markup=main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:info")
async def info_handler(callback: CallbackQuery) -> None:
    """
    Show info.

    Args:
        callback: Callback query
    """
    logger.info(f"🔘 Callback: {callback.data} | User: {callback.from_user.id if callback.from_user else 'unknown'}")

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
        "Присоединяйся! 🌿"
    )

    await callback.message.edit_text(
        text=info_text,
        reply_markup=back_to_main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:documents")
async def documents_handler(callback: CallbackQuery) -> None:
    """
    Show documents menu - always accessible.

    Args:
        callback: Callback query
    """
    logger.info(f"🔘 Callback: {callback.data} | User: {callback.from_user.id if callback.from_user else 'unknown'}")

    docs_text = (
        "📄 <b>Документы</b>\n\n"
        "Здесь вы можете ознакомиться со всеми юридическими документами:\n\n"
        "• <b>Оферта</b> — условия использования сервиса\n"
        "• <b>Политика конфиденциальности</b> — как мы обрабатываем ваши данные\n"
        "• <b>Согласие</b> — на обработку персональных данных\n\n"
        "Выберите документ для просмотра 👇"
    )

    buttons = [
        [InlineKeyboardButton(text="📄 Оферта", callback_data="agreement:offer")],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="agreement:privacy")],
        [InlineKeyboardButton(text="📋 Согласие на обработку данных", callback_data="agreement:consent")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="menu:main")],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)

    await callback.message.edit_text(
        text=docs_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()
