"""Tariff keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import settings


def tariffs_keyboard() -> InlineKeyboardMarkup:
    """
    Create tariff selection keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    # Calculate prices in rubles
    price_30 = settings.payment.TARIFF_30_PRICE // 100
    price_90 = settings.payment.TARIFF_90_PRICE // 100
    price_365 = settings.payment.TARIFF_365_PRICE // 100

    buttons = [
        [
            InlineKeyboardButton(
                text=_("💎 {days} days - {price} ₽").format(days=30, price=price_30),
                callback_data="tariff:30",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("💎 {days} days - {price} ₽").format(days=90, price=price_90),
                callback_data="tariff:90",
            )
        ],
        [
            InlineKeyboardButton(
                text=_("💎 {days} days - {price} ₽").format(days=365, price=price_365),
                callback_data="tariff:365",
            )
        ],
        [InlineKeyboardButton(text=_("« Back"), callback_data="menu:main")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
