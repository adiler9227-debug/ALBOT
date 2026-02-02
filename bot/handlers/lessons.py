"""Lesson handlers."""

from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, URLInputFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, main_keyboard, tariffs_keyboard
from bot.services import get_lesson_progress, mark_lesson_watched, mark_reminder_sent, start_lesson

router = Router(name="lessons")


async def send_reminder_task(bot: Bot, user_id: int, session: AsyncSession) -> None:
    """
    Send reminder after delay if lesson not watched.

    Args:
        bot: Bot instance
        user_id: User ID
        session: Database session
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
                "Всего 8 минут - и ты увидишь в чём настоящая причина твоей тревоги "
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


@router.callback_query(F.data == "lesson:watch")
async def lesson_watch_handler(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
) -> None:
    """
    Handle watch lesson button.

    Args:
        callback: Callback query
        bot: Bot instance
        session: Database session
    """
    if not callback.from_user:
        return

    user_id = callback.from_user.id

    # Start lesson (create or update progress)
    await start_lesson(session, user_id)

    # Start reminder task
    asyncio.create_task(send_reminder_task(bot, user_id, session))
    logger.info(f"Started reminder task for user {user_id}")

    # Send lesson text
    lesson_text = (
        "Я практикую уже более 6 лет и тема тревожности - одна из самых частых в моей работе. \n\n"
        "Как и обещала, отправляю тебе урок, обязательно посмотри его: \n"
        "✅ Если ты давно находишься в тяжелом эмоциональном состоянии \n"
        "✅ Если сложно расслабиться даже в спокойной обстановке \n"
        "✅ Если вся энергия уходит на тревожные переживания и крутящиеся мысли \n"
        "✅ Если тревога стала фоном и мешает мыслить ясно \n"
        "✅ Часто чувствуешь волнение и внутреннюю дрожь \n\n"
        "И если ты уже пробовала разные способы: \n"
        "- ходила к психологам, глотала таблетки (седативные, антидепрессанты), искала поддержку у близких и друзей. Но тревога не отпускает, возвращается снова и снова. \n\n"
        "Этот урок про другой способ. Через тело и дыхание. \n\n"
        "⏱ Всего 8 минут. \n"
        "Найди тихое место, нажми 'play' и просто следуй за голосом 👇"
    )

    # 1. Send text as a new message (as requested)
    await callback.message.answer(
        text=lesson_text,
        reply_markup=back_to_main_keyboard(),
    )
    
    # Optional: Delete the previous message with the button to avoid clutter
    try:
        await callback.message.delete()
    except Exception:
        pass

    # 2. Send video separately immediately after
    if settings.payment.PRACTICE_VIDEO_FILE_ID:
        try:
            await callback.message.answer_video(
                video=settings.payment.PRACTICE_VIDEO_FILE_ID,
                caption="🎥 Вот твоё видео с дыхательной практикой",
                reply_markup=back_to_main_keyboard(),
            )
        except Exception as e:
            logger.error(f"Failed to send lesson video: {e}")
            # Fallback to text placeholder
            await callback.message.answer(
                "🎥 Вот твоё видео с дыхательной практикой: \n\n[Видео будет здесь] (не удалось загрузить)",
                reply_markup=back_to_main_keyboard(),
            )
    elif settings.payment.LESSON_VIDEO_URL:
        try:
            if settings.payment.LESSON_VIDEO_URL.startswith("http"):
                video = URLInputFile(settings.payment.LESSON_VIDEO_URL)
            else:
                # Assume it's a file_id or local path
                video = settings.payment.LESSON_VIDEO_URL
            
            await callback.message.answer_video(
                video=video,
                caption="🎥 Вот твоё видео с дыхательной практикой",
                reply_markup=back_to_main_keyboard(),
            )
        except Exception as e:
            logger.error(f"Failed to send lesson video: {e}")
            # Fallback to text placeholder
            await callback.message.answer(
                "🎥 Вот твоё видео с дыхательной практикой: \n\n[Видео будет здесь] (не удалось загрузить)",
                reply_markup=back_to_main_keyboard(),
            )
    else:
        # Placeholder if no video URL configured
        await callback.message.answer(
            "🎥 Вот твоё видео с дыхательной практикой: \n\n[Видео будет здесь]",
            reply_markup=back_to_main_keyboard(),
        )

    await callback.answer("Урок начался")


@router.callback_query(F.data == "lesson:join")
async def lesson_join_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """
    Handle join breathing club button.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    # Mark lesson as watched
    await mark_lesson_watched(session, callback.from_user.id)

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

    await callback.message.edit_text(
        text=join_text,
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer("Выбери тариф")
