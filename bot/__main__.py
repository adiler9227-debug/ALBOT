"""Bot entry point - Railway optimized."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

# DEBUG: Print to confirm module is loading
print("=" * 60, flush=True)
print("🔧 DEBUG: bot/__main__.py is being imported", flush=True)
print("=" * 60, flush=True)

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger
from redis.asyncio import Redis

from bot.core.config import settings
from bot.database import create_engine, sessionmaker
from bot.handlers import get_handlers_router
from bot.handlers.prodamus_webhook import setup_webhook_handlers
from bot.middlewares import register_middlewares
from bot.scheduler import setup_scheduler

# =========================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Удаляем стандартный handler loguru, добавляем свой
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# =========================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# =========================
BOT_ALIVE = False
bot: Bot | None = None
dp: Dispatcher | None = None
runner: web.AppRunner | None = None


# =========================
# HEALTHCHECK ENDPOINTS
# =========================
async def health_handler(request: web.Request) -> web.Response:
    """
    Health check endpoint с информацией о статусе бота.

    Returns:
        JSON с статусом приложения
    """
    status = "alive" if BOT_ALIVE else "starting"
    return web.json_response({
        "status": "ok",
        "bot": status,
        "version": "1.0.0"
    })


async def root_handler(request: web.Request) -> web.Response:
    """Root endpoint для Railway."""
    return web.Response(text="OK")


# =========================
# WEB SERVER
# =========================
async def start_web_server() -> web.AppRunner:
    """
    Запускает aiohttp веб-сервер для healthcheck и webhooks.

    Returns:
        AppRunner для управления сервером
    """
    logger.info("🌐 Creating aiohttp application")

    app = web.Application()

    # Store bot and session maker in app context (для webhook handler)
    app["bot"] = bot
    app["session_maker"] = sessionmaker

    # Setup webhook routes (Prodamus)
    setup_webhook_handlers(app)

    # Add health endpoints
    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_handler)

    # Create and start runner
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.success(f"✅ Web server started on 0.0.0.0:{port}")
    logger.success("✅ Healthcheck endpoint is READY at /health")

    return runner


# =========================
# BOT LOGIC
# =========================
async def start_bot_safe(bot_instance: Bot, dp_instance: Dispatcher) -> None:
    """
    Запускает бота с retry логикой и обработкой ошибок.

    Args:
        bot_instance: Экземпляр бота
        dp_instance: Экземпляр диспетчера
    """
    global BOT_ALIVE

    max_retries = 5
    backoff = 5  # секунды

    logger.info("🤖 Starting bot polling with retry logic")

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Bot polling attempt {attempt}/{max_retries}")

            BOT_ALIVE = True
            await dp_instance.start_polling(bot_instance)

            # Если polling завершился нормально (не ошибка)
            logger.info("✅ Bot polling stopped normally")
            return

        except Exception as e:
            BOT_ALIVE = False
            logger.error(f"❌ Bot polling failed (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                logger.info(f"⏳ Retrying in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff
            else:
                logger.error("🚨 Max retries reached. Bot stopped.")
                logger.warning("⚠️ Web server continues running for healthcheck")

    # Держим процесс живым даже если бот упал
    logger.info("💤 Keeping process alive (web server only)")
    while True:
        await asyncio.sleep(3600)


# =========================
# GRACEFUL SHUTDOWN
# =========================
async def shutdown(signal_name: str | None = None) -> None:
    """
    Graceful shutdown приложения.

    Args:
        signal_name: Название сигнала (SIGTERM, SIGINT)
    """
    global bot, dp, runner

    logger.warning(f"🛑 {'Received ' + signal_name + ' signal. ' if signal_name else ''}Shutting down...")

    # 1. Остановка бота
    if dp:
        try:
            await dp.stop_polling()
            logger.info("✅ Bot polling stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

    # 2. Закрытие бота
    if bot:
        try:
            await bot.session.close()
            logger.info("✅ Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot: {e}")

    # 3. Остановка веб-сервера
    if runner:
        try:
            await runner.cleanup()
            logger.info("✅ Web server stopped")
        except Exception as e:
            logger.error(f"Error stopping web server: {e}")

    logger.success("👋 Application shutdown complete")


# =========================
# STARTUP LOGIC
# =========================
async def on_startup(bot_instance: Bot) -> None:
    """
    Actions on bot startup.

    Args:
        bot_instance: Bot instance
    """
    logger.info("🚀 Bot startup sequence initiated")

    try:
        # Setup scheduler (non-critical)
        scheduler = setup_scheduler(bot_instance)
        scheduler.start()
        logger.success("⏰ Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {e}")
        logger.warning("⚠️ Continuing without scheduler")


# =========================
# MAIN
# =========================
async def main() -> None:
    """Основная функция запуска приложения."""
    global bot, dp, runner

    logger.info("=" * 60)
    logger.info("🚀 STARTING APPLICATION")
    logger.info("=" * 60)

    try:
        # === 1. Инициализация БД ===
        logger.info("📦 Creating database engine")
        create_engine()
        logger.success("✅ Database engine created")

        # === 2. Инициализация хранилища ===
        try:
            if settings.redis.REDIS_URL:
                logger.info("🔄 Attempting to connect to Redis...")
                redis = Redis.from_url(
                    settings.redis.REDIS_URL,
                    decode_responses=False
                )
                storage = RedisStorage(redis=redis)
                logger.success("📦 Using Redis storage")
            else:
                logger.warning("⚠️ REDIS_URL not set")
                storage = MemoryStorage()
                logger.info("📦 Using Memory storage")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Redis: {e}")
            logger.info("📦 Falling back to Memory storage")
            storage = MemoryStorage()

        # === 3. Создание бота ===
        logger.info("🤖 Creating bot instance")
        bot = Bot(
            token=settings.bot.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        logger.success("✅ Bot instance created")

        # === 4. Создание диспетчера ===
        logger.info("📡 Creating dispatcher")
        dp = Dispatcher(storage=storage)
        register_middlewares(dp)
        dp.include_router(get_handlers_router())
        dp.startup.register(on_startup)
        logger.success("✅ Dispatcher configured")

        # === 5. ЗАПУСК WEB СЕРВЕРА ПЕРВЫМ ===
        logger.info("🌐 Starting web server (PRIORITY #1)")
        runner = await start_web_server()

        # === 6. Пауза для прохождения healthcheck ===
        logger.info("⏳ Waiting 2 seconds for Railway healthcheck...")
        await asyncio.sleep(2)
        logger.success("✅ Healthcheck window passed")

        # === 7. Запуск бота в фоновой задаче ===
        logger.info("🤖 Starting bot in background task")
        bot_task = asyncio.create_task(start_bot_safe(bot, dp))

        # === 8. Регистрация обработчиков сигналов ===
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s.name))
            )
        logger.success("✅ Signal handlers registered")

        # === 9. Держим процесс живым ===
        logger.success("=" * 60)
        logger.success("✅ APPLICATION STARTED SUCCESSFULLY")
        logger.success("📡 Bot polling in background")
        logger.success("🩺 Healthcheck: http://0.0.0.0:{}/health".format(os.getenv("PORT", 8080)))
        logger.success("=" * 60)

        # Ждем завершения бота (или бесконечно)
        await bot_task

    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received")
    except Exception as e:
        logger.exception(f"🚨 FATAL ERROR: {e}")
    finally:
        await shutdown()


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    # Install uvloop для производительности
    try:
        uvloop.install()
        logger.info("🌀 uvloop installed")
    except ImportError:
        logger.warning("⚠️ uvloop not available, using default asyncio")

    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"💥 Application crashed: {e}")
        sys.exit(1)
