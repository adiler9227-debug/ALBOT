import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from handlers import client, admin, payments, posts, schedule, settings
from database.db import init_db, get_scheduled_posts, update_scheduled_post_status
from handlers.settings import get_current_channel_id
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# Webhook настройки
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "") + WEBHOOK_PATH if os.getenv("RAILWAY_PUBLIC_DOMAIN") else None
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

async def publish_scheduled_posts():
    """Публикация отложенных постов"""
    try:
        posts_list = await get_scheduled_posts()
        now = datetime.now()
        
        for post in posts_list:
            if post['status'] == 'pending' and datetime.fromisoformat(post['publish_time']) <= now:
                try:
                    channel_id = get_current_channel_id()
                    await bot.send_message(
                        chat_id=channel_id,
                        text=post['content']
                    )
                    await update_scheduled_post_status(post['id'], 'published')
                    logger.info(f"Опубликован отложенный пост ID {post['id']}")
                except Exception as e:
                    logger.error(f"Ошибка публикации поста {post['id']}: {e}")
                    await update_scheduled_post_status(post['id'], 'failed')
    except Exception as e:
        logger.error(f"Ошибка в publish_scheduled_posts: {e}")

async def on_startup():
    """Действия при запуске"""
    await init_db()
    
    # Подключаем роутеры
    dp.include_router(settings.router)
    dp.include_router(client.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)
    dp.include_router(posts.router)
    dp.include_router(schedule.router)
    
    # Запускаем планировщик для отложенных постов
    scheduler.add_job(publish_scheduled_posts, 'interval', minutes=1)
    scheduler.start()
    logger.info("Планировщик запущен")
    
    # Устанавливаем webhook если есть домен
    if WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {WEBHOOK_URL}")
    else:
        logger.warning("RAILWAY_PUBLIC_DOMAIN не найден, webhook не установлен")
    
    logger.info("Бот запущен!")

async def on_shutdown():
    """Действия при остановке"""
    scheduler.shutdown()
    await bot.delete_webhook()
    await bot.session.close()

def main():
    """Основная функция"""
    # Создаем веб-приложение
    app = web.Application()
    
    # Настройка webhook
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настройка приложения
    setup_application(app, dp, bot=bot)
    
    # Колбэки запуска/остановки
    app.on_startup.append(lambda app: on_startup())
    app.on_shutdown.append(lambda app: on_shutdown())
    
    # Запуск веб-сервера
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == '__main__':
    main()
