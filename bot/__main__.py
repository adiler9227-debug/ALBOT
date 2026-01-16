"""Bot entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import uvloop
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
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


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for Railway."""
    return web.Response(text="OK", status=200)


async def start_webhook_server(bot: Bot) -> None:
    """
    Start aiohttp webhook server FIRST.

    Args:
        bot: Bot instance
    """
    app = web.Application()

    # Store bot and session maker in app context
    app["bot"] = bot
    app["session_maker"] = sessionmaker

    # Setup webhook routes
    setup_webhook_handlers(app)

    # Add health check endpoints
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    # Get port from environment (Railway provides PORT)
    port = int(os.getenv("PORT", 8080))

    logger.info(f"Starting webhook server on 0.0.0.0:{port}")

    # Create runner and start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"✅ Webhook server started successfully on port {port}")
    logger.info(f"✅ Health check available at http://0.0.0.0:{port}/health")

    # Keep server running forever
    while True:
        await asyncio.sleep(3600)


async def start_bot_polling(bot: Bot, dp: Dispatcher) -> None:
    """
    Start bot polling AFTER web server is up.

    Args:
        bot: Bot instance
        dp: Dispatcher instance
    """
    # Wait a bit to ensure web server is fully ready for healthcheck
    await asyncio.sleep(2)

    logger.info("🤖 Starting bot polling...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Bot polling error: {e}")
        # Don't crash - web server must stay alive for healthcheck
        raise


async def on_startup(bot: Bot) -> None:
    """
    Actions on bot startup.

    Args:
        bot: Bot instance
    """
    logger.info("✅ Bot startup initiated")

    try:
        # Setup scheduler (non-critical)
        scheduler = setup_scheduler(bot)
        scheduler.start()
        logger.info("✅ Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {e}")


async def on_shutdown(bot: Bot) -> None:
    """
    Actions on bot shutdown.

    Args:
        bot: Bot instance
    """
    logger.info("🛑 Bot stopped")
    await bot.session.close()


async def main() -> None:
    """Main entry point."""
    # Setup logging to stdout for Railway
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        force=True,
    )

    logger.info("=" * 60)
    logger.info("🚀 ALBOT Starting...")
    logger.info("=" * 60)

    # Log environment
    logger.info(f"📊 Railway: {'PORT' in os.environ}")
    logger.info(f"🔑 Bot token: {'✅' if settings.bot.BOT_TOKEN else '❌'}")
    logger.info(f"🗄️ Database: {'✅' if settings.db.DATABASE_URL else '❌'}")
    logger.info(f"🔴 Redis: {'✅' if settings.cache.REDIS_URL else '❌'}")

    # Choose storage based on Redis availability
    storage = MemoryStorage()
    try:
        if settings.cache.REDIS_URL:
            logger.info("🔴 Attempting Redis connection...")
            redis = Redis.from_url(settings.cache.REDIS_URL, decode_responses=False)
            await redis.ping()
            storage = RedisStorage(redis=redis)
            logger.info("✅ Redis storage connected")
        else:
            logger.info("💾 Using memory storage (no Redis)")
    except Exception as e:
        logger.warning(f"⚠️ Redis failed: {e}, using memory storage")
        storage = MemoryStorage()

    # Create bot instance
    logger.info("🤖 Creating bot instance...")
    bot = Bot(
        token=settings.bot.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("✅ Bot instance created")

    # Create dispatcher
    logger.info("⚙️ Creating dispatcher...")
    dp = Dispatcher(storage=storage)

    # Register middlewares
    logger.info("🔧 Registering middlewares...")
    register_middlewares(dp)

    # Register handlers
    logger.info("📝 Registering handlers...")
    dp.include_router(get_handlers_router())

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("=" * 60)
    logger.info("✅ All components initialized")
    logger.info("🚀 Starting services...")
    logger.info("=" * 60)

    # CRITICAL: Start web server FIRST (for Railway healthcheck), then bot
    try:
        # Create tasks - web server must start before healthcheck
        webhook_task = asyncio.create_task(start_webhook_server(bot))
        bot_task = asyncio.create_task(start_bot_polling(bot, dp))

        # Wait for both (return_exceptions=True prevents crash)
        await asyncio.gather(webhook_task, bot_task, return_exceptions=True)

    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        await on_shutdown(bot)


if __name__ == "__main__":
    # Use uvloop for better performance
    uvloop.install()

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ FATAL: {e}", exc_info=True)
        sys.exit(1)
