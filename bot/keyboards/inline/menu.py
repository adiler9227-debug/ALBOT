"""Main menu keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_keyboard() -> InlineKeyboardMarkup:
    """
    Create main menu keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="🫁 Watch Breathing Lesson", callback_data="lesson:watch")],
        [InlineKeyboardButton(text="🌿 Join Breathing Club", callback_data="lesson:join")],
        [InlineKeyboardButton(text="👤 My Account", callback_data="menu:account")],
        [InlineKeyboardButton(text="🎁 Bonuses", callback_data="bonuses")],
        [InlineKeyboardButton(text="ℹ️ Info", callback_data="menu:info")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """
    Create back to main menu keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="« Back to Menu", callback_data="menu:main")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
