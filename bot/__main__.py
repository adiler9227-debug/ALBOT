"""Bot entry point."""

from __future__ import annotations

import asyncio
import logging

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger
from redis.asyncio import Redis

from bot.core.config import settings
from bot.handlers import get_handlers_router
from bot.middlewares import register_middlewares
from bot.scheduler import setup_scheduler

# Use uvloop for better performance
uvloop.install()


async def on_startup(bot: Bot) -> None:
    """
    Execute actions on startup.

    Args:
        bot: Bot instance
    """
    logger.info("Bot started")

    # Setup scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started")


async def on_shutdown(bot: Bot) -> None:
    """
    Execute actions on shutdown.

    Args:
        bot: Bot instance
    """
    logger.info("Bot shutting down")
    await bot.session.close()


async def main() -> None:
    """Main function to start the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not settings.bot.DEBUG else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create bot instance
    bot = Bot(
        token=settings.bot.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    # Create storage
    if settings.cache.REDIS_HOST:
        try:
            redis = Redis.from_url(settings.cache.redis_url)
            storage = RedisStorage(redis=redis)
            logger.info("Using Redis storage")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using memory storage")
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
        logger.info("Using memory storage")

    # Create dispatcher
    dp = Dispatcher(storage=storage)

    # Register middlewares
    register_middlewares(dp)

    # Register handlers
    dp.include_router(get_handlers_router())

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
