"""Bot entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger
from redis.asyncio import Redis

from bot.core.config import settings
from bot.database import sessionmaker
from bot.handlers import get_handlers_router
from bot.handlers.prodamus_webhook import setup_webhook_handlers
from bot.middlewares import register_middlewares
from bot.scheduler import setup_scheduler


async def on_startup(bot: Bot) -> None:
    """
    Execute actions on startup.

    Args:
        bot: Bot instance
    """
    logger.info("✅ Bot startup initiated")

    try:
        # Setup scheduler
        scheduler = setup_scheduler(bot)
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {e}")


async def on_shutdown(bot: Bot) -> None:
    """
    Execute actions on shutdown.

    Args:
        bot: Bot instance
    """
    logger.info("🛑 Bot shutting down")
    await bot.session.close()


async def start_webhook_server(bot: Bot) -> None:
    """
    Start aiohttp webhook server.

    Args:
        bot: Bot instance
    """
    logger.info("🌐 Initializing webhook server...")

    app = web.Application()

    # Store bot and session maker in app context
    app["bot"] = bot
    app["session_maker"] = sessionmaker

    # Setup webhook routes
    setup_webhook_handlers(app)

    # Get port from environment (Railway provides PORT)
    port = int(os.getenv("PORT", 8080))

    logger.info(f"🚀 Starting webhook server on 0.0.0.0:{port}")

    # Create runner
    runner = web.AppRunner(app)
    await runner.setup()

    # Create site
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"✅ Webhook server READY on 0.0.0.0:{port}")
    logger.info(f"📍 Health check: http://0.0.0.0:{port}/health")

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("🛑 Webhook server shutting down")
    except Exception as e:
        logger.error(f"❌ Webhook server error: {e}")
    finally:
        await runner.cleanup()


async def start_bot_polling(bot: Bot, dp: Dispatcher) -> None:
    """
    Start bot polling.

    Args:
        bot: Bot instance
        dp: Dispatcher instance
    """
    try:
        logger.info("🤖 Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except asyncio.CancelledError:
        logger.info("🛑 Bot polling stopped")
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")
        raise


async def main() -> None:
    """Main function to start the bot."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    logger.info("=" * 60)
    logger.info("🚀 ALBOT Starting...")
    logger.info("=" * 60)

    # Log environment info
    logger.info(f"📊 Environment: Railway={'PORT' in os.environ}")
    logger.info(f"🔑 Bot token: {'✅ Set' if settings.bot.BOT_TOKEN else '❌ Missing'}")
    logger.info(f"🗄️ Database URL: {'✅ Set' if settings.db.DATABASE_URL else '❌ Using defaults'}")
    logger.info(f"🔴 Redis URL: {'✅ Set' if settings.cache.REDIS_URL else '❌ Using defaults'}")

    # Create bot instance
    logger.info("🤖 Creating bot instance...")
    bot = Bot(
        token=settings.bot.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    logger.info("✅ Bot instance created")

    # Create storage
    storage = MemoryStorage()
    logger.info("💾 Using memory storage (default)")

    # Try to connect to Redis
    if settings.cache.REDIS_URL or settings.cache.REDIS_HOST != "localhost":
        try:
            logger.info("🔴 Attempting Redis connection...")
            redis = Redis.from_url(settings.cache.redis_url)
            await redis.ping()
            storage = RedisStorage(redis=redis)
            logger.info("✅ Connected to Redis storage")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using memory storage")
            storage = MemoryStorage()

    # Create dispatcher
    logger.info("⚙️ Creating dispatcher...")
    dp = Dispatcher(storage=storage)

    # Register middlewares
    logger.info("🔧 Registering middlewares...")
    register_middlewares(dp)

    # Register handlers
    logger.info("📝 Registering handlers...")
    dp.include_router(get_handlers_router())

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("=" * 60)
    logger.info("✅ All components initialized")
    logger.info("🚀 Starting services...")
    logger.info("=" * 60)

    # Run both bot polling and webhook server concurrently
    try:
        async with asyncio.TaskGroup() as tg:
            # Start webhook server FIRST (for Railway healthcheck)
            tg.create_task(start_webhook_server(bot))

            # Give webhook server time to start
            await asyncio.sleep(2)

            # Start bot polling
            tg.create_task(start_bot_polling(bot, dp))

    except* Exception as eg:
        logger.error("=" * 60)
        logger.error("❌ FATAL ERROR in TaskGroup:")
        for exc in eg.exceptions:
            logger.error(f"  - {type(exc).__name__}: {exc}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ FATAL: {type(e).__name__}: {e}")
        sys.exit(1)
