"""User service."""

from __future__ import annotations

import datetime

from aiogram.types import User
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import AgreementModel, LessonProgressModel, UserModel


async def add_user(session: AsyncSession, user: User, referrer: str | None = None) -> UserModel:
    """
    Add new user to database.

    Args:
        session: Database session
        user: Telegram User object
        referrer: Referrer username

    Returns:
        UserModel
    """
    new_user = UserModel(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
        referrer=referrer,
        is_premium=user.is_premium or False,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info(f"Added new user: {user.id} (@{user.username})")
    return new_user


async def user_exists(session: AsyncSession, user_id: int) -> bool:
    """
    Check if user exists in database.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if user exists, False otherwise
    """
    query = select(UserModel.id).filter_by(id=user_id).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def get_user(session: AsyncSession, user_id: int) -> UserModel | None:
    """
    Get user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        UserModel or None
    """
    query = select(UserModel).filter_by(id=user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def is_admin(session: AsyncSession, user_id: int) -> bool:
    """
    Check if user is admin.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if user is admin, False otherwise
    """
    user = await get_user(session, user_id)
    return user.is_admin if user else False


async def check_agreement(session: AsyncSession, user_id: int) -> bool:
    """
    Check if user has agreed to terms.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if user has agreed, False otherwise
    """
    query = select(AgreementModel).filter_by(user_id=user_id)
    result = await session.execute(query)
    agreement = result.scalar_one_or_none()

    # Проверяем все три согласия
    if not agreement:
        return False

    return (
        agreement.agreed_to_offer and
        agreement.agreed_to_privacy and
        agreement.agreed_to_consent
    )


async def set_agreement(session: AsyncSession, user_id: int) -> AgreementModel:
    """
    Set user agreement to terms.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        AgreementModel
    """
    query = select(AgreementModel).filter_by(user_id=user_id)
    result = await session.execute(query)
    agreement = result.scalar_one_or_none()

    if agreement:
        agreement.agreed_to_offer = True
        agreement.agreed_to_privacy = True
        agreement.agreed_to_consent = True
        agreement.updated_at = datetime.datetime.utcnow()
    else:
        agreement = AgreementModel(
            user_id=user_id,
            agreed_to_offer=True,
            agreed_to_privacy=True,
            agreed_to_consent=True,
        )
        session.add(agreement)

    await session.commit()
    await session.refresh(agreement)
    logger.info(f"User {user_id} agreed to terms")
    return agreement


async def get_lesson_progress(session: AsyncSession, user_id: int) -> LessonProgressModel | None:
    """
    Get user lesson progress.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        LessonProgressModel or None
    """
    query = select(LessonProgressModel).filter_by(user_id=user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def start_lesson(session: AsyncSession, user_id: int) -> LessonProgressModel:
    """
    Mark lesson as started for user.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        LessonProgressModel
    """
    progress = await get_lesson_progress(session, user_id)

    if progress:
        if not progress.first_lesson_started_at:
            progress.first_lesson_started_at = datetime.datetime.utcnow()
        progress.lesson_clicked = False
        progress.reminder_sent = False
    else:
        progress = LessonProgressModel(
            user_id=user_id,
            first_lesson_started_at=datetime.datetime.utcnow(),
            lesson_clicked=False,
            reminder_sent=False,
        )
        session.add(progress)

    await session.commit()
    await session.refresh(progress)
    logger.info(f"Lesson started for user {user_id}")
    return progress


async def mark_lesson_clicked(session: AsyncSession, user_id: int) -> None:
    """
    Mark lesson as clicked.

    Args:
        session: Database session
        user_id: User ID
    """
    progress = await get_lesson_progress(session, user_id)
    if progress:
        progress.lesson_clicked = True
        await session.commit()
        logger.info(f"Lesson clicked for user {user_id}")


async def mark_reminder_sent(session: AsyncSession, user_id: int) -> None:
    """
    Mark reminder as sent.

    Args:
        session: Database session
        user_id: User ID
    """
    progress = await get_lesson_progress(session, user_id)
    if progress:
        progress.reminder_sent = True
        await session.commit()
        logger.info(f"Reminder sent for user {user_id}")
