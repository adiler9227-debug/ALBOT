"""Menu handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from bot.keyboards.inline import main_keyboard

router = Router(name="menu")


@router.callback_query(F.data == "menu:main")
async def main_menu_handler(callback: CallbackQuery) -> None:
    """
    Show main menu.

    Args:
        callback: Callback query
    """
    menu_text = _(
        "🏠 Main Menu\n\n"
        "Choose an action:"
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

    info_text = _(
        "ℹ️ About the Bot\n\n"
        "This bot is your guide to the world of breathing practices and Kundalini yoga.\n\n"
        "Created by: Alina Bazhenova\n"
        "Experience: 6+ years\n\n"
        "What you'll get:\n"
        "• Breathing practices\n"
        "• Kundalini yoga classes\n"
        "• Anxiety and stress management techniques\n"
        "• Improved sleep and well-being\n"
        "• Increased energy and confidence\n\n"
        "Join us! 🌿"
    )

    await callback.message.edit_text(
        text=info_text,
        reply_markup=back_to_main_keyboard(),
    )
    await callback.answer()
