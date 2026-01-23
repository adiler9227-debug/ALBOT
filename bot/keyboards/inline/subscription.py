"""Subscription keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard() -> InlineKeyboardMarkup:
    """
    Create subscription/account keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="📅 Осталось дней", callback_data="subscription:days_left")],
        [InlineKeyboardButton(text="💰 История платежей", callback_data="subscription:history")],
        [InlineKeyboardButton(text="💳 Купить подписку", callback_data="subscription:buy")],
        [InlineKeyboardButton(text="« Назад", callback_data="menu:main")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()


def back_to_account_keyboard() -> InlineKeyboardMarkup:
    """
    Create back to account keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="« Назад к аккаунту", callback_data="menu:account")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()


def buy_subscription_keyboard() -> InlineKeyboardMarkup:
    """
    Create buy subscription keyboard (single button).

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="Продлить подписку", callback_data="subscription:buy")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
