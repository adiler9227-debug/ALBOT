"""Prodamus webhook handler."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from aiohttp import web
from aiogram import Bot
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.core.config import settings
from bot.database.models import ReferralModel
from bot.services.channel import add_to_channel
from bot.services.prodamus import create_payment, update_payment_status
from bot.services.subscriptions import extend_subscription


def verify_prodamus_signature(data: dict[str, Any], signature: str) -> bool:
    """
    Verify Prodamus webhook signature.

    Args:
        data: Webhook payload data
        signature: HMAC signature from request

    Returns:
        True if signature is valid
    """
    # Build sign string from sorted parameters
    sign_string = ";".join(f"{k}:{v}" for k, v in sorted(data.items()) if k != "sign")

    # Calculate expected signature
    expected_signature = hmac.new(
        settings.payment.PRODAMUS_SECRET_KEY.encode(),
        sign_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def handle_prodamus_webhook(
    request: web.Request,
) -> web.Response:
    """
    Handle Prodamus payment webhook.

    Args:
        request: aiohttp request

    Returns:
        aiohttp response
    """
    try:
        # Diagnostic: Read raw body
        raw_body = await request.read()
        logger.info(f"RAW BODY LEN = {len(raw_body)}")
        logger.info(f"SECRET LEN = {len(settings.payment.PRODAMUS_SECRET_KEY)}")

        # Parse form data from raw body
        try:
            decoded_body = raw_body.decode('utf-8')
            # parse_qsl returns list of (key, value)
            from urllib.parse import parse_qsl
            data_list = parse_qsl(decoded_body, keep_blank_values=True)
            data_dict = dict(data_list)
        except Exception as e:
            logger.error(f"Failed to parse raw body: {e}")
            return web.Response(status=400, text="Bad request")

        logger.info(f"Received Prodamus webhook: {data_dict.get('order_id', 'unknown')}")

        # Verify signature
        signature = data_dict.get("sign", "")
        if not verify_prodamus_signature(data_dict, signature):
            logger.error("Invalid Prodamus webhook signature")
            return web.Response(status=403, text="Invalid signature")

        # Extract payment data
        order_id = data_dict.get("order_id")
        payment_status = data_dict.get("status")
        payment_id = data_dict.get("payment_id")
        customer_email = data_dict.get("customer_email")

        if not order_id:
            logger.error("Missing order_id in webhook")
            return web.Response(status=400, text="Missing order_id")

        # Parse order_id format: "user_{user_id}_days_{days}_{timestamp}[_promo_{code}]"
        try:
            parts = order_id.split("_")
            user_id = int(parts[1])
            subscription_days = int(parts[3])
            
            # Check for promo
            promo_code = None
            if "promo" in parts:
                promo_index = parts.index("promo")
                if len(parts) > promo_index + 1:
                    promo_code = parts[promo_index + 1]
                    
        except (IndexError, ValueError):
            logger.error(f"Invalid order_id format: {order_id}")
            return web.Response(status=400, text="Invalid order_id format")

        # Get bot and session from app context
        bot: Bot = request.app["bot"]
        session_maker: async_sessionmaker[AsyncSession] = request.app["session_maker"]

        async with session_maker() as session:
            # Update or create payment record
            if payment_status == "success":
                # Update payment status
                payment = await update_payment_status(session, payment_id, "success")

                if not payment:
                    # Create payment if not exists (e.g. if we didn't save pending state)
                    try:
                        amount = float(data_dict.get("sum", 0))
                    except (ValueError, TypeError):
                        amount = 0
                        
                    payment = await create_payment(
                        session=session,
                        user_id=user_id,
                        amount=int(amount),
                        subscription_days=subscription_days,
                        payment_id=payment_id,
                        status="success"
                    )

                # Extend subscription
                await extend_subscription(session, user_id, subscription_days)

                # Record promocode usage if present
                if promo_code:
                    from sqlalchemy import select
                    promo_query = select(PromocodeModel).filter_by(code=promo_code)
                    promo_result = await session.execute(promo_query)
                    promocode = promo_result.scalar_one_or_none()
                    
                    if promocode:
                        await record_promocode_usage(session, user_id, promocode)

                # Check if this is a referral - give bonus to referrer
                await process_referral_bonus(session, user_id)

                # Add user to channel
                invite_link = await add_to_channel(bot, user_id, settings.payment.CHANNEL_ID)

                # Send success message to user
                message_text = (
                    f"✅ <b>Оплата успешно получена!</b>\n\n"
                    f"📅 Подписка активна на {subscription_days} дней\n"
                    f"🔗 Присоединяйтесь к каналу: {invite_link}\n\n"
                    f"Приятной практики! 🧘‍♀️"
                )

                try:
                    await bot.send_message(user_id, message_text)
                except Exception as e:
                    logger.error(f"Failed to send success message to user {user_id}: {e}")

                logger.info(f"Payment success for user {user_id}: {subscription_days} days")

            elif payment_status == "failed":
                await update_payment_status(session, payment_id, "failed")
                logger.warning(f"Payment failed for user {user_id}")

                # Send failure message
                try:
                    await bot.send_message(
                        user_id,
                        "❌ К сожалению, оплата не прошла. Попробуйте еще раз или обратитесь в поддержку."
                    )
                except Exception as e:
                    logger.error(f"Failed to send failure message to user {user_id}: {e}")

        return web.Response(status=200, text="OK")

    except Exception as e:
        logger.exception(f"Error processing Prodamus webhook: {e}")
        return web.Response(status=500, text="Internal server error")


async def process_referral_bonus(session: AsyncSession, referred_user_id: int, bot: Bot) -> None:
    """
    Process referral bonus - give +30 days to referrer when referred user pays.

    Args:
        session: Database session
        referred_user_id: User who just paid
        bot: Bot instance
    """
    from sqlalchemy import select

    # Find referral record
    query = select(ReferralModel).filter_by(
        referred_id=referred_user_id,
        is_bonus_given=False,
    )
    result = await session.execute(query)
    referral = result.scalar_one_or_none()

    if not referral:
        return

    # Give bonus to referrer
    referrer_id = referral.referrer_id
    bonus_days = settings.payment.REFERRAL_BONUS_DAYS

    await extend_subscription(session, referrer_id, bonus_days)

    # Mark bonus as given
    referral.is_bonus_given = True
    from datetime import datetime
    referral.bonus_given_at = datetime.utcnow()
    await session.commit()

    logger.info(f"Gave referral bonus to user {referrer_id}: +{bonus_days} days")

    # Notify referrer
    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=(
                f"🎁 <b>Поздравляем!</b>\n\n"
                f"Твой друг оплатил подписку!\n"
                f"Тебе начислено <b>+{bonus_days} дней</b> бонусной подписки.\n\n"
                f"Продолжай приглашать друзей и получай больше бонусов!"
            )
        )
        logger.info(f"Sent referral bonus notification to user {referrer_id}")
    except Exception as e:
        logger.error(f"Failed to send referral bonus notification to user {referrer_id}: {e}")


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for Railway."""
    return web.Response(text="OK", status=200)


def setup_webhook_handlers(app: web.Application) -> None:
    """
    Setup webhook routes.

    Args:
        app: aiohttp application
    """
    app.router.add_post("/prodamus-webhook", handle_prodamus_webhook)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)  # Root endpoint also responds to health checks
