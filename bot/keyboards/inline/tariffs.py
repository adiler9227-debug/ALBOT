"""Tariff keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import settings


def tariffs_keyboard() -> InlineKeyboardMarkup:
    """
    Create tariff selection keyboard.

    Returns:
        InlineKeyboardMarkup
    """
    # Prices are already in rubles
    price_7 = settings.payment.TARIFF_7_PRICE
    price_30 = settings.payment.TARIFF_30_PRICE
    price_90 = settings.payment.TARIFF_90_PRICE
    price_180 = settings.payment.TARIFF_180_PRICE
    price_365 = settings.payment.TARIFF_365_PRICE

    buttons = [
        [
            InlineKeyboardButton(
                text=f"🌱 7 дней - {price_7} ₽",
                callback_data="tariff:7",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📅 30 дней - {price_30} ₽",
                callback_data="tariff:30",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📆 90 дней - {price_90} ₽ (-20%)",
                callback_data="tariff:90",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🌟 180 дней - {price_180} ₽ (-25%)",
                callback_data="tariff:180",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⭐ 365 дней - {price_365} ₽ (-35%)",
                callback_data="tariff:365",
            )
        ],
        [InlineKeyboardButton(text="« Back", callback_data="menu:main")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
