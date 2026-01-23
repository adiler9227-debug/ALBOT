"""Subscription handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from bot.keyboards.inline import (
    agreement_keyboard,
    back_to_account_keyboard,
    subscription_keyboard,
    tariffs_keyboard,
)
from bot.services import check_agreement, get_days_left, get_payment_history

router = Router(name="subscription")


@router.callback_query(F.data == "menu:account")
async def account_menu_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show account menu.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    logger.info(f"🔘 Callback: {callback.data} - User {callback.from_user.id}")

    # Check agreement
    if not await check_agreement(session, callback.from_user.id):
        logger.warning(f"⛔ User {callback.from_user.id} tried to access account without agreement")
        agreement_text = (
            f"👋 Привет, {callback.from_user.first_name}!\n\n"
            "Чтобы продолжить, ознакомьтесь с документами и примите условия использования.\n\n"
            "Нажмите на кнопки ниже 👇"
        )
        await callback.message.edit_text(
            text=agreement_text,
            reply_markup=agreement_keyboard(),
        )
        await callback.answer("Требуется согласие")
        return

    account_text = (
        "👤 Мой аккаунт\n\n"
        "Здесь ты можешь:\n"
        "• Проверить остаток дней подписки\n"
        "• Посмотреть историю платежей\n"
        "• Купить или продлить подписку"
    )

    try:
        await callback.message.edit_text(
            text=account_text,
            reply_markup=subscription_keyboard(),
        )
    except TelegramBadRequest:
        pass
        
    await callback.answer()


@router.callback_query(F.data == "subscription:days_left")
async def days_left_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show days left in subscription.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    logger.info(f"Checking days for user {callback.from_user.id}")
    days = await get_days_left(session, callback.from_user.id)
    
    if days is None:
        # Check if user has payments despite no active subscription
        payments = await get_payment_history(session, callback.from_user.id, limit=1)
        if payments:
            days_text = (
                "⚠️ <b>Подписка не найдена, но есть платежи</b>\n\n"
                "Мы видим ваши платежи, но активная подписка не найдена.\n"
                "Возможно, срок действия истек или произошла ошибка активации.\n"
                "Попробуйте нажать кнопку «История оплат» или обратитесь в поддержку."
            )
        else:
            days_text = (
                "❌ Нет данных о подписке\n\n"
                "Похоже, у тебя еще нет истории подписок.\n"
                "Начни свое путешествие прямо сейчас!"
            )
    elif days > 0:
        logger.info(f"User {callback.from_user.id} has {days} days")
        days_text = (
            f"📅 Статус подписки\n\n"
            f"✅ Подписка активна\n"
            f"Осталось дней: {days}\n\n"
        )

        if days <= 7:
            days_text += "⚠️ Не забудь продлить подписку!"
    else:
        logger.info(f"User {callback.from_user.id} has expired subscription")
        days_text = (
            "❌ Нет активной подписки\n\n"
            "У тебя нет активной подписки.\n"
            "Купи подписку, чтобы получить доступ ко всем материалам!"
        )

    try:
        await callback.message.edit_text(
            text=days_text,
            reply_markup=back_to_account_keyboard(),
        )
    except TelegramBadRequest:
        pass
        
    await callback.answer()


@router.callback_query(F.data == "subscription:history")
async def payment_history_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show payment history.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    logger.info(f"Checking history for user {callback.from_user.id}")
    
    # 6.1 Запрос (using service which now uses created_at)
    payments = await get_payment_history(session, callback.from_user.id, limit=10)
    
    logger.info(f"User {callback.from_user.id} has {len(payments) if payments else 0} payments")

    # 6.2 Отображение
    if not payments:
        text = "❌ У вас пока нет оплат"
        # Using edit_text to keep UI clean, or answer if requested. 
        # User example used message.answer, but this is a menu navigation.
        # I'll use edit_text with back button.
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_account_keyboard(),
        )
        return

    text = "📜 История оплат:\n\n"
    for p in payments:
        # Safe access with getattr not strictly needed if p is PaymentModel, 
        # but good practice if p could be dict. Here p is PaymentModel.
        pid = p.payment_id or "N/A"
        amt = p.amount
        date_str = p.created_at.strftime("%d.%m.%Y")
        
        text += (
            f"💳 ID: {pid}\n"
            f"💰 {amt} ₽\n"
            f"📅 {date_str}\n\n"
        )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=back_to_account_keyboard(),
        )
    except TelegramBadRequest:
        pass
        
    await callback.answer()


@router.callback_query(F.data == "subscription:buy")
async def buy_subscription_handler(callback: CallbackQuery) -> None:
    """
    Show tariff selection.

    Args:
        callback: Callback query
    """
    tariff_text = (
        "💳 Купить подписку\n\n"
        "Выбери срок подписки:\n"
        "Чем дольше срок - тем выгоднее! 🎁"
    )

    try:
        await callback.message.edit_text(
            text=tariff_text,
            reply_markup=tariffs_keyboard(),
        )
    except TelegramBadRequest:
        pass
        
    await callback.answer()
