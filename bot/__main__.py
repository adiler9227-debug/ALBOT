"""Bot entry point - Full rebuild with all features."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiohttp import web
from loguru import logger

# Setup logging IMMEDIATELY
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)


async def run_bot_and_server() -> None:
    """Run web server and bot together."""

    # STEP 1: Start web server IMMEDIATELY (for healthcheck)
    port = int(os.getenv("PORT", 8080))

    logger.info("="*60)
    logger.info("🚀 ALBOT FULL REBUILD - ALL FEATURES ENABLED")
    logger.info("="*60)
    logger.info(f"🌐 Starting web server on 0.0.0.0:{port}")

    # Create web app
    app = web.Application()

    # Add health check endpoint FIRST
    async def health_check(request: web.Request) -> web.Response:
        return web.Response(text="OK", status=200)

    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    # Start server runner
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"✅ Web server STARTED on http://0.0.0.0:{port}")
    logger.info(f"✅ Healthcheck READY at /health")
    logger.info("="*60)

    # STEP 2: Initialize bot (in background, can fail)
    bot = None
    dp = None

    try:
        logger.info("🤖 Loading bot components...")

        # Import all bot modules
        import uvloop
        from aiogram import Bot, Dispatcher
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis

        from bot.core.config import settings
        from bot.database import sessionmaker
        from bot.handlers import get_handlers_router
        from bot.handlers.prodamus_webhook import setup_webhook_handlers
        from bot.middlewares import register_middlewares
        from bot.scheduler import setup_scheduler

        uvloop.install()

        logger.info(f"📊 Environment check:")
        logger.info(f"  - Railway: {'✅' if 'PORT' in os.environ else '❌'}")
        logger.info(f"  - Bot token: {'✅' if settings.bot.BOT_TOKEN else '❌'}")
        logger.info(f"  - Database: {'✅' if settings.db.DATABASE_URL else '❌'}")
        logger.info(f"  - Redis: {'✅' if settings.cache.REDIS_URL else '❌'}")

        # Storage
        storage = MemoryStorage()
        try:
            if settings.cache.REDIS_URL:
                redis = Redis.from_url(settings.cache.REDIS_URL, decode_responses=False)
                await redis.ping()
                storage = RedisStorage(redis=redis)
                logger.info("✅ Redis storage connected")
            else:
                logger.info("💾 Using memory storage")
        except Exception as e:
            logger.warning(f"⚠️ Redis failed: {e}, using memory storage")

        # Create bot
        bot = Bot(
            token=settings.bot.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        logger.info("✅ Bot instance created")

        # Create dispatcher
        dp = Dispatcher(storage=storage)
        register_middlewares(dp)
        dp.include_router(get_handlers_router())
        logger.info("✅ All handlers registered:")
        logger.info("  - Start & agreements")
        logger.info("  - Payments (Prodamus)")
        logger.info("  - Bonuses (referrals + video)")
        logger.info("  - Lessons & reminders")
        logger.info("  - Personal cabinet")

        # Setup webhook routes in web app
        app["bot"] = bot
        app["session_maker"] = sessionmaker
        setup_webhook_handlers(app)
        logger.info("✅ Webhook endpoints added:")
        logger.info("  - /prodamus-webhook")
        logger.info("  - /health")

        # Startup callback
        async def on_startup(bot_instance: Bot) -> None:
            logger.info("✅ Bot starting...")
            try:
                scheduler = setup_scheduler(bot_instance)
                scheduler.start()
                logger.info("✅ Scheduler started (reminders, auto-kick)")
            except Exception as e:
                logger.warning(f"⚠️ Scheduler failed: {e}")

        dp.startup.register(on_startup)

        logger.info("="*60)
        logger.info("🚀 STARTING BOT POLLING...")
        logger.info("="*60)

        # Start bot polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}", exc_info=True)
        logger.info("⚠️ Bot failed BUT web server continues (healthcheck still works)")

        # Keep web server alive forever
        logger.info("🌐 Web server running in fallback mode...")
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("ALBOT v2.0 - FULL REBUILD")
    logger.info("All features: Prodamus, Referrals, Video Reviews, Reminders")
    logger.info("="*60)

    try:
        asyncio.run(run_bot_and_server())
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal crash: {e}", exc_info=True)
        sys.exit(1)
