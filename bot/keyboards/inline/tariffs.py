"""Tariff keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import settings


def get_tariffs_data() -> dict:
    """Get tariffs data with current prices."""
    return {
        "7": {
            "title": "Подписка на 7 дней",
            "description": "Доступ ко всем практикам на неделю",
            "price": settings.payment.TARIFF_7_PRICE,
            "days": 7,
            "label": f"7 дней - {settings.payment.TARIFF_7_PRICE} ₽"
        },
        "30": {
            "title": "Подписка на 30 дней",
            "description": "Месяц осознанности и спокойствия",
            "price": settings.payment.TARIFF_30_PRICE,
            "days": 30,
            "label": f"30 дней - {settings.payment.TARIFF_30_PRICE} ₽"
        },
        "90": {
            "title": "Подписка на 90 дней",
            "description": "Три месяца практики со скидкой 20%",
            "price": settings.payment.TARIFF_90_PRICE,
            "days": 90,
            "label": f"90 дней - {settings.payment.TARIFF_90_PRICE} ₽ (-20%)"
        },
        "180": {
            "title": "Подписка на 180 дней",
            "description": "Полгода развития со скидкой 25%",
            "price": settings.payment.TARIFF_180_PRICE,
            "days": 180,
            "label": f"180 дней - {settings.payment.TARIFF_180_PRICE} ₽ (-25%)"
        },
        "365": {
            "title": "Подписка на 365 дней",
            "description": "Год новой жизни со скидкой 35%",
            "price": settings.payment.TARIFF_365_PRICE,
            "days": 365,
            "label": f"365 дней - {settings.payment.TARIFF_365_PRICE} ₽ (-35%)"
        }
    }


TARIFFS = get_tariffs_data()  # For backward compatibility if needed, but better to call function to get dynamic settings


def tariffs_keyboard(urls: dict | None = None, labels: dict | None = None) -> InlineKeyboardMarkup:
    """
    Create tariff selection keyboard.

    Args:
        urls: Dictionary of tariff_id -> url (optional)
        labels: Dictionary of tariff_id -> label (optional)

    Returns:
        InlineKeyboardMarkup
    """
    tariffs = get_tariffs_data()
    
    buttons = []
    for tariff_id, data in tariffs.items():
        label = labels.get(tariff_id, data["label"]) if labels else data["label"]
        
        button_kwargs = {"text": label}
        
        if urls and tariff_id in urls:
            button_kwargs["url"] = urls[tariff_id]
        else:
            button_kwargs["callback_data"] = f"tariff:{tariff_id}"
            
        buttons.append([InlineKeyboardButton(**button_kwargs)])
    
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="menu:main")])

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
