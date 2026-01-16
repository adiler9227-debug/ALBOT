"""Prodamus payment service."""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlencode

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database.models import PaymentModel, PromocodeModel, PromocodeUsageModel


def generate_payment_url(
    order_id: str,
    amount: int,
    customer_email: str | None = None,
    customer_phone: str | None = None,
    products: str | None = None,
) -> str:
    """
    Generate Prodamus payment URL with HMAC signature.

    Args:
        order_id: Unique order identifier
        amount: Amount in rubles
        customer_email: Customer email (optional)
        customer_phone: Customer phone (optional)
        products: Product description (optional)

    Returns:
        Full payment URL
    """
    params = {
        "order_id": order_id,
        "customer_email": customer_email or "",
        "customer_phone": customer_phone or "",
        "products[0][price]": str(amount),
        "products[0][quantity]": "1",
        "products[0][name]": products or "Подписка на занятия",
        "sys": "club-breathing",
    }

    # Remove empty parameters
    params = {k: v for k, v in params.items() if v}

    # Generate signature
    sign_string = ";".join(f"{k}:{v}" for k, v in sorted(params.items()))
    signature = hmac.new(
        settings.payment.PRODAMUS_SECRET_KEY.encode(),
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()

    params["sign"] = signature

    # Build URL
    base_url = f"https://{settings.payment.PRODAMUS_DOMAIN}/pay"
    return f"{base_url}?{urlencode(params)}"


async def apply_promocode(
    session: AsyncSession,
    user_id: int,
    code: str,
    base_amount: int,
) -> tuple[int, PromocodeModel | None]:
    """
    Apply promocode and return discounted amount.

    Args:
        session: Database session
        user_id: User ID
        code: Promocode string
        base_amount: Base amount before discount

    Returns:
        Tuple of (final_amount, promocode_model or None)
    """
    # Find promocode
    query = select(PromocodeModel).filter_by(code=code.upper(), is_active=True)
    result = await session.execute(query)
    promocode = result.scalar_one_or_none()

    if not promocode:
        logger.warning(f"Promocode '{code}' not found or inactive")
        return base_amount, None

    # Check if user already used this promocode
    usage_query = select(PromocodeUsageModel).filter_by(
        user_id=user_id,
        promocode_id=promocode.id
    )
    usage_result = await session.execute(usage_query)
    if usage_result.scalar_one_or_none():
        logger.warning(f"User {user_id} already used promocode '{code}'")
        return base_amount, None

    # Check max uses
    if promocode.max_uses is not None and promocode.current_uses >= promocode.max_uses:
        logger.warning(f"Promocode '{code}' reached max uses limit")
        return base_amount, None

    # Apply discount
    final_amount = max(0, base_amount - promocode.discount_amount)
    logger.info(f"Applied promocode '{code}': {base_amount} → {final_amount} RUB")

    return final_amount, promocode


async def record_promocode_usage(
    session: AsyncSession,
    user_id: int,
    promocode: PromocodeModel,
) -> None:
    """
    Record promocode usage.

    Args:
        session: Database session
        user_id: User ID
        promocode: Promocode model
    """
    # Create usage record
    usage = PromocodeUsageModel(
        user_id=user_id,
        promocode_id=promocode.id,
    )
    session.add(usage)

    # Increment usage counter
    promocode.current_uses += 1

    await session.commit()
    logger.info(f"Recorded promocode usage: user {user_id}, code '{promocode.code}'")


async def create_payment(
    session: AsyncSession,
    user_id: int,
    amount: int,
    subscription_days: int,
    payment_id: str | None = None,
    status: str = "pending",
) -> PaymentModel:
    """
    Create payment record.

    Args:
        session: Database session
        user_id: User ID
        amount: Amount in rubles
        subscription_days: Number of days
        payment_id: Prodamus payment ID
        status: Payment status (pending, success, failed)

    Returns:
        PaymentModel
    """
    payment = PaymentModel(
        user_id=user_id,
        amount=amount,
        currency="RUB",
        subscription_days=subscription_days,
        payment_provider="prodamus",
        payment_id=payment_id,
        status=status,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    logger.info(f"Created payment record for user {user_id}: {amount} RUB, {subscription_days} days")
    return payment


async def update_payment_status(
    session: AsyncSession,
    payment_id: str,
    status: str,
) -> PaymentModel | None:
    """
    Update payment status by payment_id.

    Args:
        session: Database session
        payment_id: Prodamus payment ID
        status: New status (success, failed)

    Returns:
        Updated PaymentModel or None if not found
    """
    query = select(PaymentModel).filter_by(payment_id=payment_id)
    result = await session.execute(query)
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = status
        await session.commit()
        await session.refresh(payment)
        logger.info(f"Updated payment {payment_id} status to '{status}'")

    return payment
