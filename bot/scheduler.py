"""Scheduler for background tasks."""

from __future__ import annotations

import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select

from bot.core.config import settings
from bot.database import sessionmaker
from bot.database.models import LessonProgressModel, SubscriptionModel
from bot.services import (
    deactivate_subscription, 
    get_expired_subscriptions, 
    get_expiring_subscriptions,
    remove_from_channel
)
from bot.keyboards.inline import buy_subscription_keyboard


async def kick_expired_users(bot: Bot) -> None:
    """
    Kick users with expired subscriptions from channel.

    Args:
        bot: Bot instance
    """
    logger.info("Starting expired subscriptions check")

    try:
        async with sessionmaker() as session:
            # Get expired subscriptions
            expired_subscriptions = await get_expired_subscriptions(session)

            if not expired_subscriptions:
                logger.info("No expired subscriptions found")
                return

            logger.info(f"Found {len(expired_subscriptions)} expired subscriptions")

            for subscription in expired_subscriptions:
                try:
                    # Remove from channel
                    success = await remove_from_channel(bot, subscription.user_id)

                    if success:
                        # Deactivate subscription
                        await deactivate_subscription(session, subscription.user_id)

                        # Send notification to user
                        try:
                            await bot.send_message(
                                chat_id=subscription.user_id,
                                text=(
                                    "❌ Your subscription has expired\n\n"
                                    "You have been removed from the channel.\n\n"
                                    "To continue learning, renew your subscription in the bot."
                                ),
                            )
                        except Exception as e:
                            logger.error(f"Failed to send notification to user {subscription.user_id}: {e}")

                        logger.info(f"Successfully processed expired subscription for user {subscription.user_id}")
                    else:
                        logger.warning(f"Failed to kick user {subscription.user_id} from channel")

                except Exception as e:
                    logger.error(f"Error processing expired subscription for user {subscription.user_id}: {e}")

            logger.info("Finished expired subscriptions check")

    except Exception as e:
        logger.error(f"Error in kick_expired_users: {e}")


async def send_lesson_reminders(bot: Bot) -> None:
    """
    Send reminders to users who watched free lesson 48-72h ago but didn't purchase.

    Args:
        bot: Bot instance
    """
    logger.info("Starting lesson reminders check")

    try:
        async with sessionmaker() as session:
            # Calculate time window (48-72 hours ago)
            now = datetime.datetime.now(datetime.timezone.utc)
            time_72h_ago = now - datetime.timedelta(seconds=settings.payment.REMINDER_48H_SECONDS + 86400)
            time_48h_ago = now - datetime.timedelta(seconds=settings.payment.REMINDER_48H_SECONDS)

            # Find users who watched lesson but didn't purchase
            query = (
                select(LessonProgressModel)
                .filter(
                    LessonProgressModel.watched_free_lesson == True,  # noqa: E712
                    LessonProgressModel.reminder_sent == False,  # noqa: E712
                    LessonProgressModel.free_lesson_watched_at.between(time_72h_ago, time_48h_ago),
                )
            )
            result = await session.execute(query)
            lesson_progress_list = result.scalars().all()

            if not lesson_progress_list:
                logger.info("No users need lesson reminders")
                return

            logger.info(f"Found {len(lesson_progress_list)} users to send lesson reminders")

            for lesson_progress in lesson_progress_list:
                try:
                    await send_lesson_reminder(bot, session, lesson_progress)
                except Exception as e:
                    logger.error(f"Failed to send reminder to user {lesson_progress.user_id}: {e}")

            logger.info("Finished lesson reminders check")

    except Exception as e:
        logger.error(f"Error in send_lesson_reminders: {e}")


async def send_expiry_reminders(bot: Bot) -> None:
    """
    Send reminders to users whose subscription expires in 3 days.

    Args:
        bot: Bot instance
    """
    logger.info("Starting expiry reminders check")

    try:
        async with sessionmaker() as session:
            # Get subscriptions expiring in 3 days
            subscriptions = await get_expiring_subscriptions(session, days=3)

            if not subscriptions:
                logger.info("No subscriptions expiring soon")
                return

            logger.info(f"Found {len(subscriptions)} subscriptions expiring soon")

            for subscription in subscriptions:
                try:
                    # Send reminder
                    await bot.send_message(
                        chat_id=subscription.user_id,
                        text=(
                            "Напоминаю 🌿\n\n"
                            "Через 3 дня заканчивается доступ в клуб.\n"
                            "Буду рада продолжить практики вместе 🤍"
                        ),
                        reply_markup=buy_subscription_keyboard(),
                    )

                    logger.info(f"Sent expiry reminder to user {subscription.user_id}")

                except Exception as e:
                    logger.error(f"Error sending expiry reminder to user {subscription.user_id}: {e}")

            logger.info("Finished expiry reminders check")

    except Exception as e:
        logger.error(f"Error in send_expiry_reminders: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Setup and configure scheduler.

    Args:
        bot: Bot instance

    Returns:
        Configured AsyncIOScheduler
    """
    scheduler = AsyncIOScheduler()

    # Add job to check expired subscriptions every day at 00:00
    scheduler.add_job(
        kick_expired_users,
        trigger="cron",
        hour=0,
        minute=0,
        args=[bot],
        id="kick_expired_users",
        replace_existing=True,
    )

    # Add job to send lesson reminders every 6 hours
    scheduler.add_job(
        send_lesson_reminders,
        trigger="cron",
        hour="*/6",
        minute=0,
        args=[bot],
        id="send_lesson_reminders",
        replace_existing=True,
    )

    # Add job to send expiry reminders every day at 10:00
    scheduler.add_job(
        send_expiry_reminders,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        id="send_expiry_reminders",
        replace_existing=True,
    )

    logger.info(
        "Scheduler configured:\n"
        "- Expired subscriptions check: daily at 00:00\n"
        "- Lesson reminders: every 6 hours\n"
        "- Expiry reminders: daily at 10:00"
    )

    return scheduler
