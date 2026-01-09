"""Scheduler for background tasks."""

from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from bot.database import sessionmaker
from bot.services import deactivate_subscription, get_expired_subscriptions, remove_from_channel


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

    logger.info("Scheduler configured: checking expired subscriptions daily at 00:00")

    return scheduler
