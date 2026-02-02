"""Reply menu handlers."""

from __future__ import annotations

import asyncio
import datetime

from aiogram import Bot, F, Router
from aiogram.types import Message, URLInputFile, FSInputFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, tariffs_keyboard
from bot.services import (
    get_days_left,
    get_payment_history,
    start_lesson,
    mark_lesson_watched,
    mark_reminder_sent,
    get_lesson_progress
)

router = Router(name="reply_menu")


async def send_reminder_task(bot: Bot, user_id: int, session: AsyncSession) -> None:
    """
    Send reminder after delay if lesson not watched.
    """
    try:
        await asyncio.sleep(settings.payment.REMINDER_DELAY_SECONDS)

        progress = await get_lesson_progress(session, user_id)
        if not progress or progress.watched_free_lesson or progress.reminder_sent:
            return

        try:
            photo_url = settings.payment.SAD_CAT_PHOTO_URL
            if photo_url.startswith("http"):
                photo = URLInputFile(photo_url)
            else:
                photo = FSInputFile(photo_url)

            reminder_text = (
                "😿 Нежное напоминание 🤍\n\n"
                "Ты еще не посмотрела урок по дыханию. "
                "Возможно отвлеклась - это нормально.\n\n"
                "Просто знай: эта практика помогает:\n"
                "— снизить тревожность\n"
                "— успокоить поток мыслей\n"
                "— восстановить силы и энергию\n\n"
                "В нём я делюсь проверенным подходом, который помогает справиться с тревогой самостоятельно, "
                "без долгой и дорогой работы с психологами или специалистами.\n\n"
                "Всего 10 минут - и ты увидишь в чём настоящая причина твоей тревоги "
                "и как с ней работать в любой момент.\n\n"
                "Нажми на кнопку и посмотри урок прямо сейчас ⬇️"
            )

            await bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=reminder_text,
                reply_markup=back_to_main_keyboard(),
            )

            await mark_reminder_sent(session, user_id)
            logger.info(f"Sent reminder to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in reminder task for user {user_id}: {e}")


@router.message(F.text == "🫁 Урок по дыханию")
async def lesson_button_handler(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Handle lesson button."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    await start_lesson(session, user_id)

    # Start reminder task
    asyncio.create_task(send_reminder_task(bot, user_id, session))

    lesson_text = (
        "Я практикую уже более 6 лет и тема тревожности - одна из самых частых в моей работе.\n\n"
        "Как и обещала, отправляю тебе урок, обязательно посмотри его:\n"
        "✅ Если давно находишься в тяжелом эмоциональном состоянии\n"
        "✅ Если сложно расслабиться даже в спокойной обстановке\n"
        "✅ Если вся энергия уходит на тревожные переживания\n"
        "✅ Если тревога стала фоном и мешает мыслить ясно\n"
        "✅ Часто чувствуешь волнение и внутреннюю дрожь\n\n"
        "⏱ Всего 10 минут.\n"
        "Найди тихое место, нажми 'play' и просто следуй за голосом 👆"
    )

    try:
        video = settings.payment.PRACTICE_VIDEO_FILE_ID or settings.payment.LESSON_VIDEO_URL
        if video:
            await message.answer_video(
                video=video,
                caption=lesson_text,
                reply_markup=back_to_main_keyboard(),
            )
        else:
            await message.answer(
                text=lesson_text + "\n\n[Видео недоступно]",
                reply_markup=back_to_main_keyboard(),
            )
    except Exception as e:
        logger.error(f"Failed to send lesson video: {e}")
        await message.answer(
            text=lesson_text + "\n\n[Не удалось загрузить видео]",
            reply_markup=back_to_main_keyboard(),
        )


@router.message(F.text == "🌿 Клуб дыхания")
@router.message(F.text == "💳 Продлить подписку")
async def club_button_handler(message: Message, session: AsyncSession) -> None:
    """Handle club/subscribe button."""
    if not message.from_user:
        return

    # Mark lesson as watched just in case (optional, but consistent with flow)
    await mark_lesson_watched(session, message.from_user.id)

    join_text = (
        "🌿 Вступить в клуб дыхания\n\n"
        "Получи доступ к:\n"
        "• Ежедневным дыхательным практикам\n"
        "• Занятиям по кундалини-йоге\n"
        "• Закрытому чату сообщества\n"
        "• Личной поддержке от Алины\n\n"
        "Выбери срок подписки:"
    )

    await message.answer(
        text=join_text,
        reply_markup=tariffs_keyboard(),
    )


@router.message(F.text == "📅 Дней осталось")
async def days_left_button_handler(message: Message, session: AsyncSession) -> None:
    """Handle days left button."""
    if not message.from_user:
        return

    days = await get_days_left(session, message.from_user.id)
    
    if days is None:
        payments = await get_payment_history(session, message.from_user.id, limit=1)
        if payments:
            days_text = (
                "⚠️ <b>Подписка не найдена, но есть платежи</b>\n\n"
                "Мы видим ваши платежи, но активная подписка не найдена.\n"
                "Возможно, срок действия истек или произошла ошибка активации.\n"
                "Попробуйте нажать кнопку «История оплат» или обратитесь в поддержку."
            )
        else:
            days_text = (
                "❌ Нет данных о подписке\n\n"
                "Похоже, у тебя еще нет истории подписок.\n"
                "Начни свое путешествие прямо сейчас!"
            )
    elif days == 0:
        days_text = (
            "⌛ <b>Срок действия подписки истек</b>\n\n"
            "Ваша подписка закончилась. Продлите её, чтобы продолжить занятия!"
        )
    else:
        days_text = (
            f"📅 <b>До конца подписки: {days} дн.</b>\n\n"
            "Продолжайте заниматься и укреплять свое здоровье! 🌿"
        )

    await message.answer(text=days_text)


@router.message(F.text == "💬 Служба заботы")
async def support_button_handler(message: Message) -> None:
    """Handle support button."""
    support_text = (
        "💬 <b>Служба заботы</b>\n\n"
        "Если у вас возникли вопросы или технические сложности, напишите нам:\n"
        "@alina_breathing_support"
    )
    await message.answer(text=support_text)
