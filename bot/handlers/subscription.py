"""Subscription handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import back_to_account_keyboard, subscription_keyboard, tariffs_keyboard
from bot.services import get_days_left, get_payment_history

router = Router(name="subscription")


@router.callback_query(F.data == "menu:account")
async def account_menu_handler(callback: CallbackQuery) -> None:
    """
    Show account menu.

    Args:
        callback: Callback query
    """
    account_text = _(
        "👤 My Account\n\n"
        "Here you can:\n"
        "• Check days left in subscription\n"
        "• View payment history\n"
        "• Buy or extend subscription"
    )

    await callback.message.edit_text(
        text=account_text,
        reply_markup=subscription_keyboard(),
    )
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

    days = await get_days_left(session, callback.from_user.id)

    if days > 0:
        days_text = _(
            "📅 Subscription Status\n\n"
            "✅ Active subscription\n"
            "Days left: {days}\n\n"
        ).format(days=days)

        if days <= 7:
            days_text += "⚠️ Don't forget to renew your subscription!"
    else:
        days_text = _(
            "❌ No Active Subscription\n\n"
            "You don't have an active subscription.\n"
            "Buy subscription to get access to all materials!"
        )

    await callback.message.edit_text(
        text=days_text,
        reply_markup=back_to_account_keyboard(),
    )
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

    payments = await get_payment_history(session, callback.from_user.id, limit=10)

    if payments:
        history_text = "💰 Payment History\n\n"
        for payment in payments:
            date_str = payment.payment_date.strftime("%d.%m.%Y %H:%M")
            amount_str = f"{payment.amount // 100:.2f}"
            history_text += _(
                "• {date} - {amount} {currency} ({days} days)\n"
            ).format(
                date=date_str,
                amount=amount_str,
                currency=payment.currency,
                days=payment.tariff_days,
            )
    else:
        history_text = _(
            "📝 No payments yet\n\n"
            "Buy your first subscription to start learning!"
        )

    await callback.message.edit_text(
        text=history_text,
        reply_markup=back_to_account_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "subscription:buy")
async def buy_subscription_handler(callback: CallbackQuery) -> None:
    """
    Show tariff selection.

    Args:
        callback: Callback query
    """
    tariff_text = _(
        "💳 Buy Subscription\n\n"
        "Choose subscription period:\n"
        "The longer the period - the more profitable! 🎁"
    )

    await callback.message.edit_text(
        text=tariff_text,
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer()
