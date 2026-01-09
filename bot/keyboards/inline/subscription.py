"""Subscription keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard() -> InlineKeyboardMarkup:
    """
    Create subscription/account keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text=_("📅 Days Left"), callback_data="subscription:days_left")],
        [InlineKeyboardButton(text=_("💰 Payment History"), callback_data="subscription:history")],
        [InlineKeyboardButton(text=_("💳 Buy Subscription"), callback_data="subscription:buy")],
        [InlineKeyboardButton(text=_("« Back"), callback_data="menu:main")],
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
        [InlineKeyboardButton(text=_("« Back to Account"), callback_data="menu:account")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
