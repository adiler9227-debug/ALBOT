"""Payment handlers."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from aiogram.utils.i18n import gettext as _
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard
from bot.services import add_to_channel, create_payment_record, extend_subscription, mark_lesson_clicked

router = Router(name="payments")


# Tariff configuration
TARIFFS = {
    "30": {
        "days": settings.payment.TARIFF_30_DAYS,
        "price": settings.payment.TARIFF_30_PRICE,
        "title": _("1 Month Subscription"),
        "description": _("Access to breathing club for 30 days"),
    },
    "90": {
        "days": settings.payment.TARIFF_90_DAYS,
        "price": settings.payment.TARIFF_90_PRICE,
        "title": _("3 Months Subscription"),
        "description": _("Access to breathing club for 90 days"),
    },
    "365": {
        "days": settings.payment.TARIFF_365_DAYS,
        "price": settings.payment.TARIFF_365_PRICE,
        "title": _("12 Months Subscription"),
        "description": _("Access to breathing club for 365 days"),
    },
}


@router.callback_query(F.data.startswith("tariff:"))
async def tariff_selection_handler(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """
    Handle tariff selection and create invoice.

    Args:
        callback: Callback query
        bot: Bot instance
        session: Database session
    """
    if not callback.from_user or not callback.message:
        return

    # Mark lesson as clicked (user is interested)
    await mark_lesson_clicked(session, callback.from_user.id)

    # Get tariff ID
    tariff_id = callback.data.split(":")[1]
    if tariff_id not in TARIFFS:
        await callback.answer(_("Invalid tariff"), show_alert=True)
        return

    tariff = TARIFFS[tariff_id]

    try:
        # Send invoice
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=tariff["title"],
            description=tariff["description"],
            payload=f"subscription_{tariff_id}_{callback.from_user.id}",
            provider_token=settings.payment.PAYMENT_TOKEN,
            currency="RUB",
            prices=[
                LabeledPrice(
                    label=tariff["title"],
                    amount=tariff["price"],
                )
            ],
            start_parameter=f"subscription_{tariff_id}",
        )

        await callback.answer(_("Invoice sent"))
        logger.info(f"Sent invoice for tariff {tariff_id} to user {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Failed to send invoice: {e}")
        await callback.answer(_("Failed to create invoice. Please try again later."), show_alert=True)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    """
    Handle pre-checkout query.

    Args:
        pre_checkout_query: Pre-checkout query
    """
    # Validate payment (you can add custom validation here)
    await pre_checkout_query.answer(ok=True)
    logger.info(f"Pre-checkout approved for user {pre_checkout_query.from_user.id}")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, bot: Bot, session: AsyncSession) -> None:
    """
    Handle successful payment.

    Args:
        message: Message with successful payment
        bot: Bot instance
        session: Database session
    """
    if not message.from_user or not message.successful_payment:
        return

    payment_info = message.successful_payment
    user_id = message.from_user.id

    # Parse tariff from payload
    try:
        payload_parts = payment_info.invoice_payload.split("_")
        tariff_id = payload_parts[1]

        if tariff_id not in TARIFFS:
            logger.error(f"Invalid tariff ID in payload: {tariff_id}")
            return

        tariff = TARIFFS[tariff_id]

        # Create payment record
        await create_payment_record(
            session=session,
            user_id=user_id,
            amount=payment_info.total_amount,
            currency=payment_info.currency,
            tariff_days=tariff["days"],
            provider_payment_charge_id=payment_info.provider_payment_charge_id,
        )

        # Extend subscription
        subscription = await extend_subscription(
            session=session,
            user_id=user_id,
            days=tariff["days"],
        )

        # Add user to channel
        await add_to_channel(bot, user_id)

        # Send confirmation
        success_text = _(
            "✅ Payment successful!\n\n"
            "💳 Amount: {amount} {currency}\n"
            "📅 Period: {days} days\n\n"
            "Your subscription is activated! 🎉\n\n"
            "Welcome to the Breathing Club! 🌿\n"
            "Join our channel: [Channel Link]\n\n"
            "Happy learning! 🎓"
        ).format(
            amount=payment_info.total_amount // 100,
            currency=payment_info.currency,
            days=tariff["days"],
        )

        await message.answer(
            text=success_text,
            reply_markup=back_to_main_keyboard(),
        )

        logger.info(f"Successfully processed payment for user {user_id}, tariff {tariff_id}")

    except Exception as e:
        logger.error(f"Error processing successful payment: {e}")
        await message.answer(
            _("Payment received, but there was an error activating subscription. Please contact support."),
            reply_markup=back_to_main_keyboard(),
        )
