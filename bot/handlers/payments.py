"""Payment handlers."""

from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database.models import VideoReviewModel
from bot.keyboards.inline import back_to_main_keyboard, tariffs_keyboard
from bot.services.prodamus import generate_payment_url, apply_promocode

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
async def show_tariffs_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show available tariffs.

    Args:
        callback: Callback query
        session: Database session
    """
    # Check if user has video review
    video_query = select(VideoReviewModel).filter_by(user_id=callback.from_user.id)
    video_result = await session.execute(video_query)
    has_video_review = video_result.scalar_one_or_none() is not None

    urls = {}
    labels = {}
    
    timestamp = int(time.time())

    for tariff_id, tariff in TARIFFS.items():
        final_price = tariff['price']
        promo_code = None
        
        # Apply discount if user has video review
        if has_video_review:
            discounted_price, promocode = await apply_promocode(
                session=session,
                user_id=callback.from_user.id,
                code=settings.payment.VIDEO_REVIEW_PROMO,
                base_amount=tariff['price']
            )
            if promocode and discounted_price < tariff['price']:
                final_price = discounted_price
                promo_code = promocode.code

        # Generate order ID
        order_id = f"user_{callback.from_user.id}_days_{tariff['days']}_{timestamp}"
        if promo_code:
            order_id += f"_promo_{promo_code}"
            
        # Generate URL
        payment_url = generate_payment_url(
            order_id=order_id,
            amount=final_price,
            products=tariff['title']
        )
        logger.info(f"Payment URL for tariff {tariff_id}: {payment_url}")
        
        urls[tariff_id] = payment_url
        
        # Update label if discounted
        if promo_code:
            labels[tariff_id] = f"{tariff['title']} - {final_price} ₽ (скидка)"
    
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
        reply_markup=tariffs_keyboard(urls=urls, labels=labels),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def process_tariff_selection(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Process tariff selection.

    Args:
        callback: Callback query
        session: Database session
    """
    tariff_id = callback.data.split(":")[1]
    tariff = TARIFFS.get(tariff_id)

    if not tariff:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    # Check for video review and apply discount
    final_price = tariff['price']
    promo_code = None

    # Check if user has video review
    video_query = select(VideoReviewModel).filter_by(user_id=callback.from_user.id)
    video_result = await session.execute(video_query)
    if video_result.scalar_one_or_none():
        # Try to apply VIDEOOTZIV promo
        discounted_price, promocode = await apply_promocode(
            session=session,
            user_id=callback.from_user.id,
            code=settings.payment.VIDEO_REVIEW_PROMO,
            base_amount=tariff['price']
        )
        
        if promocode and discounted_price < tariff['price']:
            final_price = discounted_price
            promo_code = promocode.code

    # Generate unique order ID
    # Format: user_{user_id}_days_{days}_{timestamp}[_promo_{code}]
    timestamp = int(time.time())
    order_id = f"user_{callback.from_user.id}_days_{tariff['days']}_{timestamp}"
    
    if promo_code:
        order_id += f"_promo_{promo_code}"

    # Generate payment URL
    payment_url = generate_payment_url(
        order_id=order_id,
        amount=final_price,
        customer_email=None,
        products=tariff['title']
    )

    # Create keyboard with payment link
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"💳 Оплатить {final_price} ₽",
            url=payment_url
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« Назад к тарифам",
            callback_data="buy_subscription"
        )
    )

    text = (
        f"💳 <b>Оплата тарифа «{tariff['title']}»</b>\n\n"
        f"Стоимость: <b>{final_price} ₽</b>"
    )
    
    if promo_code:
        text += f" <s>{tariff['price']} ₽</s>\n🎁 Промокод <b>{promo_code}</b> применен!"
    else:
        text += "\n"

    text += (
        f"Срок действия: <b>{tariff['days']} дней</b>\n\n"
        f"Для оплаты перейдите по кнопке ниже 👇"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=builder.as_markup()
    )
    await callback.answer()
