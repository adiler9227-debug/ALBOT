"""Reply menu handlers."""

from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.types import FSInputFile, Message, URLInputFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_account_keyboard, back_to_main_keyboard, tariffs_keyboard
from bot.services import (
    get_days_left,
    get_lesson_progress,
    get_payment_history,
    mark_lesson_watched,
    start_lesson,
)
# We need send_reminder_task but it's not exported from lessons.py. 
# It's better to duplicate the task logic or import it if possible.
# Since it's an internal helper in lessons.py, I'll copy the logic to avoid circular imports or messing with __all__.
from bot.services import mark_reminder_sent

router = Router(name="reply_menu")


async def _send_reminder_task(bot: Bot, user_id: int, session: AsyncSession) -> None:
    """
    Send reminder after delay if lesson not watched.
    Duplicated from lessons.py to avoid circular imports.
    """
    try:
        # Wait for configured delay
        await asyncio.sleep(settings.payment.REMINDER_DELAY_SECONDS)

        # Check if lesson was watched
        progress = await get_lesson_progress(session, user_id)
        if not progress or progress.watched_free_lesson or progress.reminder_sent:
            return

        # Send reminder with sad cat
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

            # Mark reminder as sent
            await mark_reminder_sent(session, user_id)
            logger.info(f"Sent reminder to user {user_id}")

        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")

    except asyncio.CancelledError:
        logger.debug(f"Reminder task cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Error in reminder task for user {user_id}: {e}")


@router.message(F.text == "🫁 Урок по дыханию")
async def lesson_button(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Handle breathing lesson button."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    logger.info(f"User {user_id} requested lesson via reply menu")

    # Start lesson (create or update progress)
    await start_lesson(session, user_id)

    # Start reminder task
    asyncio.create_task(_send_reminder_task(bot, user_id, session))
    logger.info(f"Started reminder task for user {user_id}")

    # Send lesson video with caption
    lesson_text = (
        "Я практикую уже более 6 лет и тема тревожности - одна из самых частых в моей работе.\n\n"
        "Как и обещала, отправляю тебе урок, обязательно посмотри его:\n"
        "✅ Если давно находишься в тяжелом эмоциональном состоянии\n"
        "✅ Если сложно расслабиться даже в спокойной обстановке\n"
        "✅ Если вся энергия уходит на тревожные переживания\n"
        "✅ Если тревога стала фоном и мешает мыслить ясно\n"
        "✅ Часто чувствуешь волнение и внутреннюю дрожь\n\n"
        "⏱ Всего 10 минут.\n"
        "Найди тихое место, нажми 'play' и просто следуй за голосом 👇"
    )

    try:
        # Use PRACTICE_VIDEO_FILE_ID if available, otherwise URL
        video = settings.payment.PRACTICE_VIDEO_FILE_ID or settings.payment.LESSON_VIDEO_URL
        
        if video:
            await message.answer_video(
                video=video,
                caption=lesson_text,
                reply_markup=back_to_main_keyboard(),
            )
        else:
             # Fallback to text if no video
            await message.answer(
                text=lesson_text + "\n\n[Видео недоступно]",
                reply_markup=back_to_main_keyboard(),
            )

    except Exception as e:
        logger.error(f"Failed to send lesson video: {e}")
        # Fallback to text on error
        await message.answer(
            text=lesson_text + "\n\n[Не удалось загрузить видео]",
            reply_markup=back_to_main_keyboard(),
        )


@router.message(F.text == "🌿 Клуб дыхания")
async def club_button(message: Message, session: AsyncSession) -> None:
    """Handle join club button."""
    if not message.from_user:
        return
        
    logger.info(f"User {message.from_user.id} requested club join via reply menu")

    # Mark lesson as watched
    await mark_lesson_watched(session, message.from_user.id)

    # Show tariffs
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
async def days_left_button(message: Message, session: AsyncSession) -> None:
    """Handle days left button."""
    if not message.from_user:
        return

    logger.info(f"Checking days for user {message.from_user.id} via reply menu")
    days = await get_days_left(session, message.from_user.id)
    
    if days is None:
        # Check if user has payments despite no active subscription
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
    elif days > 0:
        logger.info(f"User {message.from_user.id} has {days} days")
        days_text = (
            f"📅 Статус подписки\n\n"
            f"✅ Подписка активна\n"
            f"Осталось дней: {days}\n\n"
        )

        if days <= 7:
            days_text += "⚠️ Не забудь продлить подписку!"
    else:
        logger.info(f"User {message.from_user.id} has expired subscription")
        days_text = (
            "❌ Нет активной подписки\n\n"
            "У тебя нет активной подписки.\n"
            "Купи подписку, чтобы получить доступ ко всем материалам!"
        )

    await message.answer(
        text=days_text,
        reply_markup=back_to_account_keyboard(),
    )


@router.message(F.text == "💳 Продлить подписку")
async def extend_subscription_button(message: Message) -> None:
    """Handle extend subscription button."""
    logger.info(f"User {message.from_user.id if message.from_user else 'unknown'} requested extension via reply menu")
    
    tariff_text = (
        "💳 Купить подписку\n\n"
        "Выбери срок подписки:\n"
        "Чем дольше срок - тем выгоднее! 🎁"
    )

    await message.answer(
        text=tariff_text,
        reply_markup=tariffs_keyboard(),
    )


@router.message(F.text == "💬 Служба заботы")
async def support_button(message: Message) -> None:
    """Handle support button."""
    logger.info(f"User {message.from_user.id if message.from_user else 'unknown'} requested support via reply menu")
    
    support_text = (
        "💬 <b>Служба заботы</b>\n\n"
        "Если у тебя возникли вопросы или проблемы, напиши нам:\n"
        "👉 @alina_bazhenova_help\n\n"
        "Мы обязательно поможем!"
    )
    
    await message.answer(
        text=support_text,
        parse_mode="HTML"
    )
