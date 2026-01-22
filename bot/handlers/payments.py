"""Payment handlers."""

from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, tariffs_keyboard
from bot.services.prodamus import generate_payment_url

router = Router(name="payments")

# Tariff configuration
TARIFFS = {
    "7": {
        "days": settings.payment.TARIFF_7_DAYS,
        "price": settings.payment.TARIFF_7_PRICE,
        "title": "Пробная неделя",
        "description": "Доступ к занятиям на 7 дней",
    },
    "30": {
        "days": settings.payment.TARIFF_30_DAYS,
        "price": settings.payment.TARIFF_30_PRICE,
        "title": "1 месяц",
        "description": "Доступ к занятиям на 30 дней",
    },
    "90": {
        "days": settings.payment.TARIFF_90_DAYS,
        "price": settings.payment.TARIFF_90_PRICE,
        "title": "3 месяца",
        "description": "Доступ к занятиям на 90 дней",
    },
    "180": {
        "days": settings.payment.TARIFF_180_DAYS,
        "price": settings.payment.TARIFF_180_PRICE,
        "title": "Полгода",
        "description": "Доступ к занятиям на 180 дней",
    },
    "365": {
        "days": settings.payment.TARIFF_365_DAYS,
        "price": settings.payment.TARIFF_365_PRICE,
        "title": "1 год",
        "description": "Доступ к занятиям на 365 дней",
    },
}


@router.callback_query(F.data == "buy_subscription")
async def show_tariffs_handler(callback: CallbackQuery) -> None:
    """
    Show available tariffs.

    Args:
        callback: Callback query
    """
    text = (
        "💎 <b>Выберите тариф:</b>\n\n"
        f"🌱 {TARIFFS['7']['title']} — {TARIFFS['7']['price']} ₽\n"
        f"📅 {TARIFFS['30']['title']} — {TARIFFS['30']['price']} ₽\n"
        f"📆 {TARIFFS['90']['title']} — {TARIFFS['90']['price']} ₽ <i>(-20%)</i>\n"
        f"🌟 {TARIFFS['180']['title']} — {TARIFFS['180']['price']} ₽ <i>(-25%)</i>\n"
        f"⭐ {TARIFFS['365']['title']} — {TARIFFS['365']['price']} ₽ <i>(-35%)</i>\n\n"
        "Выберите подходящий тариф ниже 👇"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def process_tariff_selection(callback: CallbackQuery) -> None:
    """
    Process tariff selection.

    Args:
        callback: Callback query
    """
    tariff_id = callback.data.split(":")[1]
    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    # Generate unique order ID
    # Format: user_{user_id}_days_{days}_{timestamp}
    # We append timestamp to ensure uniqueness if user clicks multiple times
    # The webhook handler will parse: user_id=parts[1], days=parts[3]
    order_id = f"user_{callback.from_user.id}_days_{tariff['days']}_{int(time.time())}"

    # Generate payment URL
    payment_url = generate_payment_url(
        order_id=order_id,
        amount=tariff['price'],
        customer_email=None,  # Prodamus will ask for email if not provided
        products=tariff['title']
    )

    # Create keyboard with payment link
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"💳 Оплатить {tariff['price']} ₽",
            url=payment_url
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад к тарифам",
            callback_data="buy_subscription"
        )
    )

    await callback.message.edit_text(
        text=(
            f"💳 <b>Оплата тарифа «{tariff['title']}»</b>\n\n"
            f"Стоимость: <b>{tariff['price']} ₽</b>\n"
            f"Срок действия: <b>{tariff['days']} дней</b>\n\n"
            f"Для оплаты перейдите по кнопке ниже 👇"
        ),
        reply_markup=builder.as_markup()
    )
    await callback.answer()
