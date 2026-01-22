"""Payment handlers."""

from __future__ import annotations

from urllib.parse import urlencode

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, tariffs_keyboard
from bot.services import mark_lesson_watched
from bot.services.prodamus import create_payment

router = Router(name="payments")


# Tariff configuration with Prodamus payment links
TARIFFS = {
    "7": {
        "days": settings.payment.TARIFF_7_DAYS,
        "price": settings.payment.TARIFF_7_PRICE,
        "title": "Пробная неделя",
        "description": "Доступ к занятиям на 7 дней",
        "payment_url": "https://payform.ru/4lanBvw/",
    },
    "30": {
        "days": settings.payment.TARIFF_30_DAYS,
        "price": settings.payment.TARIFF_30_PRICE,
        "title": "1 месяц",
        "description": "Доступ к занятиям на 30 дней",
        "payment_url": "https://payform.ru/4kanBwA/",
    },
    "90": {
        "days": settings.payment.TARIFF_90_DAYS,
        "price": settings.payment.TARIFF_90_PRICE,
        "title": "3 месяца",
        "description": "Доступ к занятиям на 90 дней",
        "payment_url": "https://payform.ru/5canBwZ/",
    },
    "180": {
        "days": settings.payment.TARIFF_180_DAYS,
        "price": settings.payment.TARIFF_180_PRICE,
        "title": "Полгода",
        "description": "Доступ к занятиям на 180 дней",
        "payment_url": "https://payform.ru/66anBxq/",
    },
    "365": {
        "days": settings.payment.TARIFF_365_DAYS,
        "price": settings.payment.TARIFF_365_PRICE,
        "title": "1 год",
        "description": "Доступ к занятиям на 365 дней",
        "payment_url": "https://payform.ru/6tanBxN/",
    },
}


def build_payment_url(base_url: str, user_id: int, days: int) -> str:
    """
    Build payment URL with order_id parameter.

    Args:
        base_url: Base Prodamus payment URL
        user_id: User ID
        days: Subscription days

    Returns:
        Full payment URL with parameters
    """
    order_id = f"user_{user_id}_days_{days}"
    params = {"order_id": order_id}
    return f"{base_url}?{urlencode(params)}"


@router.callback_query(F.data == "buy_subscription")
async def show_tariffs_handler(callback: CallbackQuery) -> None:
    """
    Show available tariffs.

    Args:
        callback: Callback query
    """
    if not callback.message:
        return

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
async def tariff_selection_handler(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
) -> None:
    """
    Handle tariff selection and show payment link.

    Args:
        callback: Callback query
        bot: Bot instance
        session: Database session
    """
    if not callback.from_user or not callback.message:
        return

    # Mark lesson as watched (user is interested)
    await mark_lesson_watched(session, callback.from_user.id)

    # Get tariff ID
    tariff_id = callback.data.split(":")[1]
    if tariff_id not in TARIFFS:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    tariff = TARIFFS[tariff_id]
    user_id = callback.from_user.id

    # Create pending payment record
    order_id = f"user_{user_id}_days_{tariff['days']}"

    await create_payment(
        session=session,
        user_id=user_id,
        amount=tariff["price"],
        subscription_days=tariff["days"],
        payment_id=order_id,
        status="pending",
    )

    # Build payment URL with order_id
    payment_url = build_payment_url(
        tariff["payment_url"],
        user_id,
        tariff["days"],
    )

    # Create inline keyboard with payment button
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=f"💳 Оплатить {tariff['price']} ₽",
            url=payment_url,
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="« Назад к тарифам",
            callback_data="buy_subscription",
        )
    )

    # Send payment message
    text = (
        f"💳 <b>Оплата подписки</b>\n\n"
        f"📦 Тариф: <b>{tariff['title']}</b>\n"
        f"📅 Срок: {tariff['days']} дней\n"
        f"💰 Стоимость: <b>{tariff['price']} ₽</b>\n\n"
        f"👇 Нажмите кнопку ниже для перехода к оплате:\n\n"
        f"После успешной оплаты вы автоматически получите:\n"
        f"✅ Доступ к каналу с занятиями\n"
        f"✅ Активацию подписки на {tariff['days']} дней\n"
        f"✅ Приветственное сообщение с инструкциями"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard.as_markup(),
    )
    await callback.answer()

    logger.info(
        f"Generated payment link for user {user_id}: "
        f"{tariff['days']} days, {tariff['price']} RUB, URL: {payment_url}"
    )
