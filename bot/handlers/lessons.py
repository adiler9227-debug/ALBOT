"""Lesson handlers."""

from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, URLInputFile
from aiogram.utils.i18n import gettext as _
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, main_keyboard, tariffs_keyboard
from bot.services import get_lesson_progress, mark_lesson_clicked, mark_reminder_sent, start_lesson

router = Router(name="lessons")


async def send_reminder_task(bot: Bot, user_id: int, session: AsyncSession) -> None:
    """
    Send reminder after delay if lesson not clicked.

    Args:
        bot: Bot instance
        user_id: User ID
        session: Database session
    """
    try:
        # Wait for configured delay
        await asyncio.sleep(settings.payment.REMINDER_DELAY_SECONDS)

        # Check if lesson was clicked
        progress = await get_lesson_progress(session, user_id)
        if not progress or progress.lesson_clicked or progress.reminder_sent:
            return

        # Send reminder with sad cat
        try:
            photo_url = settings.payment.SAD_CAT_PHOTO_URL
            if photo_url.startswith("http"):
                photo = URLInputFile(photo_url)
            else:
                photo = FSInputFile(photo_url)

            reminder_text = _(
                "😿 {name}, gentle reminder 🤍\n\n"
                "You haven't watched the breathing lesson yet. "
                "Maybe you got distracted - that's normal.\n\n"
                "Just know: this practice helps:\n"
                "— reduce anxiety\n"
                "— calm the flow of thoughts\n"
                "— restore strength and energy\n\n"
                "In it, I share a proven approach that helps you cope with anxiety on your own, "
                "without long and expensive work with psychologists or specialists.\n\n"
                "Only 8 minutes - and you will see what the real cause of your anxiety is "
                "and how to work with it at any moment.\n\n"
                "Click the button and watch the lesson right now ⬇️"
            ).format(name="User")  # We can get from DB if needed

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
    lesson_text = _(
        "I've been practicing for over 6 years and the topic of anxiety is one of the most common in my work.\n\n"
        "As promised, I'm sending you the lesson, be sure to watch it:\n"
        "✅ If you have been in a difficult emotional state for a long time\n"
        "✅ If it's hard to relax even in a calm environment\n"
        "✅ If all your energy goes into anxious experiences and spinning thoughts\n"
        "✅ If anxiety has become a background and interferes with clear thinking\n"
        "✅ Often feel excitement and inner trembling\n\n"
        "And if you've already tried different ways:\n"
        "- going to psychologists, swallowing pills (sedatives, antidepressants), "
        "seeking support from loved ones and friends. But the anxiety doesn't let go, returns again and again.\n\n"
        "This lesson is about another way. Through the body and breathing.\n\n"
        "⏱ Only 8 minutes.\n"
        "Find a quiet place, press 'play' and just follow the voice 👇"
    )

    await callback.message.edit_text(
        text=lesson_text,
        reply_markup=back_to_main_keyboard(),
    )

    # Send lesson video (you need to upload it first or use URL)
    # For now, just send a placeholder
    await callback.message.answer(
        _("🎥 Here's your breathing practice video:\n\n[Video would be here]"),
        reply_markup=back_to_main_keyboard(),
    )

    await callback.answer(_("Lesson started"))


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

    # Mark lesson as clicked
    await mark_lesson_clicked(session, callback.from_user.id)

    # Show tariffs
    join_text = _(
        "🌿 Join the Breathing Club\n\n"
        "Get access to:\n"
        "• Daily breathing practices\n"
        "• Kundalini yoga classes\n"
        "• Private community chat\n"
        "• Personal support from Alina\n\n"
        "Choose your subscription period:"
    )

    await callback.message.edit_text(
        text=join_text,
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer(_("Select tariff"))
