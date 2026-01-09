import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.db import get_expired_users
from config import CHANNEL_ID

logger = logging.getLogger(__name__)

async def kick_expired_users(bot: Bot):
    """Автоматический кик пользователей с истекшей подпиской"""
    try:
        # Получаем пользователей с истекшей подпиской
        expired_users = await get_expired_users()

        if not expired_users:
            logger.info("Нет пользователей с истекшей подпиской")
            return

        logger.info(f"Найдено {len(expired_users)} пользователей с истекшей подпиской")

        for user_id in expired_users:
            try:
                # Баним пользователя
                await bot.ban_chat_member(
                    chat_id=CHANNEL_ID,
                    user_id=user_id
                )

                # Сразу разбаниваем (оставляем просто кик)
                await bot.unban_chat_member(
                    chat_id=CHANNEL_ID,
                    user_id=user_id
                )

                logger.info(f"Пользователь {user_id} удален из канала")

                # Уведомляем пользователя
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text="""
❌ Ваша подписка истекла

Вы были удалены из канала.

Чтобы продолжить обучение, продлите подписку в боте.
"""
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

            except Exception as e:
                logger.error(f"Ошибка кика пользователя {user_id}: {e}")

        logger.info(f"Обработка истекших подписок завершена")

    except Exception as e:
        logger.error(f"Ошибка в kick_expired_users: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настройка планировщика задач"""
    scheduler = AsyncIOScheduler()

    # Добавляем задачу на каждый день в 00:00
    scheduler.add_job(
        kick_expired_users,
        'cron',
        hour=0,
        minute=0,
        args=[bot]
    )

    logger.info("Планировщик настроен: проверка подписок каждый день в 00:00")

    return scheduler
