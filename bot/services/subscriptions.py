"""Subscription service."""

from __future__ import annotations

import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import SubscriptionModel


async def get_subscription(session: AsyncSession, user_id: int) -> SubscriptionModel | None:
    """
    Get user subscription.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        SubscriptionModel or None if not found
    """
    query = select(SubscriptionModel).filter_by(user_id=user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def check_expiry(session: AsyncSession, user_id: int) -> bool:
    """
    Check if subscription is active.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if subscription is active, False otherwise
    """
    subscription = await get_subscription(session, user_id)
    if not subscription:
        return False

    if not subscription.is_active:
        return False

    return subscription.expires_at > datetime.datetime.utcnow()


async def extend_subscription(session: AsyncSession, user_id: int, days: int) -> SubscriptionModel:
    """
    Extend or create subscription.

    Args:
        session: Database session
        user_id: User ID
        days: Number of days to add

    Returns:
        SubscriptionModel
    """
    subscription = await get_subscription(session, user_id)

    if subscription:
        # Extend existing subscription
        if subscription.expires_at > datetime.datetime.utcnow():
            # Add to existing expiry date
            subscription.expires_at += datetime.timedelta(days=days)
        else:
            # Subscription expired, start from now
            subscription.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=days)

        subscription.is_active = True
        logger.info(f"Extended subscription for user {user_id} by {days} days")
    else:
        # Create new subscription
        subscription = SubscriptionModel(
            user_id=user_id,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=days),
            is_active=True,
        )
        session.add(subscription)
        logger.info(f"Created new subscription for user {user_id} for {days} days")

    await session.commit()
    await session.refresh(subscription)
    return subscription


async def get_expiring_subscriptions(session: AsyncSession, days: int) -> list[SubscriptionModel]:
    """
    Get subscriptions expiring in N days.

    Args:
        session: Database session
        days: Number of days before expiration

    Returns:
        List of expiring subscriptions
    """
    now = datetime.datetime.utcnow()
    target_date_start = now + datetime.timedelta(days=days)
    target_date_end = target_date_start + datetime.timedelta(days=1)  # Within the target day

    query = select(SubscriptionModel).filter(
        SubscriptionModel.is_active == True,  # noqa: E712
        SubscriptionModel.expires_at.between(target_date_start, target_date_end),
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_days_left(session: AsyncSession, user_id: int) -> int | None:
    """
    Get days left in subscription.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Days left (0 if no subscription or expired), or None if no subscription found
    """
    subscription = await get_subscription(session, user_id)
    if not subscription:
        return None
        
    if not subscription.is_active:
        return 0

    days_left = (subscription.expires_at - datetime.datetime.utcnow()).days
    return max(0, days_left)


async def deactivate_subscription(session: AsyncSession, user_id: int) -> None:
    """
    Deactivate subscription.

    Args:
        session: Database session
        user_id: User ID
    """
    subscription = await get_subscription(session, user_id)
    if subscription:
        subscription.is_active = False
        await session.commit()
        logger.info(f"Deactivated subscription for user {user_id}")


async def get_expired_subscriptions(session: AsyncSession) -> list[SubscriptionModel]:
    """
    Get all expired subscriptions.

    Args:
        session: Database session

    Returns:
        List of expired subscriptions
    """
    query = select(SubscriptionModel).filter(
        SubscriptionModel.is_active == True,  # noqa: E712
        SubscriptionModel.expires_at < datetime.datetime.utcnow(),
    )
    result = await session.execute(query)
    return list(result.scalars().all())
