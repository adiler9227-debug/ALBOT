"""Payment service."""

from __future__ import annotations

import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import PaymentModel


async def create_payment_record(
    session: AsyncSession,
    user_id: int,
    amount: int,
    currency: str,
    subscription_days: int,
    provider_payment_charge_id: str | None = None,
) -> PaymentModel:
    """
    Create payment record.

    Args:
        session: Database session
        user_id: User ID
        amount: Payment amount in kopecks/cents
        currency: Currency code (RUB, USD, etc.)
        subscription_days: Number of days in subscription
        provider_payment_charge_id: Provider payment charge ID

    Returns:
        PaymentModel
    """
    payment = PaymentModel(
        user_id=user_id,
        amount=amount,
        currency=currency,
        subscription_days=subscription_days,
        payment_date=datetime.datetime.utcnow(),
        provider_payment_charge_id=provider_payment_charge_id,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    logger.info(f"Created payment record for user {user_id}: {amount/100:.2f} {currency}")
    return payment


async def get_payment_history(session: AsyncSession, user_id: int, limit: int = 10) -> list[PaymentModel]:
    """
    Get user payment history.

    Args:
        session: Database session
        user_id: User ID
        limit: Number of payments to return

    Returns:
        List of PaymentModel
    """
    query = (
        select(PaymentModel)
        .filter_by(user_id=user_id)
        .order_by(PaymentModel.payment_date.desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_total_revenue(session: AsyncSession) -> dict[str, int]:
    """
    Get total revenue by currency.

    Args:
        session: Database session

    Returns:
        Dictionary with currency as key and total amount as value
    """
    query = select(PaymentModel)
    result = await session.execute(query)
    payments = result.scalars().all()

    revenue: dict[str, int] = {}
    for payment in payments:
        revenue[payment.currency] = revenue.get(payment.currency, 0) + payment.amount

    return revenue
