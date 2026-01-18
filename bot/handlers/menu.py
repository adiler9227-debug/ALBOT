"""Menu handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.inline import main_keyboard

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def main_menu_handler(callback: CallbackQuery) -> None:
    """
    Show main menu.

    Args:
        callback: Callback query
    """
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
    from bot.keyboards.inline import back_to_main_keyboard

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
