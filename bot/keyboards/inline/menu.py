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
        [InlineKeyboardButton(text="Посмотреть урок по дыханию", callback_data="lesson:watch")],
        [InlineKeyboardButton(text="Вступить в клуб дыхания", callback_data="lesson:join")],
        [InlineKeyboardButton(text="Мой аккаунт", callback_data="menu:account")],
        [InlineKeyboardButton(text="Документы", callback_data="menu:documents")],
        [InlineKeyboardButton(text="Бонусы", callback_data="bonuses")],
        [InlineKeyboardButton(text="Информация", callback_data="menu:info")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()


def documents_keyboard() -> InlineKeyboardMarkup:
    """
    Create documents menu keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="Оферта", callback_data="agreement:offer")],
        [InlineKeyboardButton(text="Политика конфиденциальности", callback_data="agreement:privacy")],
        [InlineKeyboardButton(text="Согласие на обработку данных", callback_data="agreement:consent")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="menu:main")],
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
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
