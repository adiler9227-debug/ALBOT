"""Admin handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from bot.core.config import settings

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.payment.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    """Show admin panel."""
    if not message.from_user or message.from_user.id not in settings.payment.ADMIN_IDS:
        return

    admin_menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="👥 Список подписчиков", callback_data="admin:users")],
            [InlineKeyboardButton(text="📤 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="📋 Выгрузить в Excel", callback_data="admin:export")],
            [InlineKeyboardButton(text="ℹ️ Как получить ID файла", callback_data="admin:fileid_info")],
        ]
    )

    await message.answer(
        "⚙️ Админ-панель:",
        reply_markup=admin_menu_keyboard
    )


@router.message(Command("getfileid"))
async def get_file_id(message: Message) -> None:
    """Get file ID from reply."""
    if not message.from_user:
        return

    logger.info(f"Admin command /getfileid from user {message.from_user.id}")

    if message.from_user.id not in settings.payment.ADMIN_IDS:
        logger.warning(f"Unauthorized access to /getfileid from {message.from_user.id}")
        return

    if message.reply_to_message:
        if message.reply_to_message.video:
            await message.answer(f"VIDEO file_id:\n<code>{message.reply_to_message.video.file_id}</code>", parse_mode="HTML")
        elif message.reply_to_message.photo:
            await message.answer(f"PHOTO file_id:\n<code>{message.reply_to_message.photo[-1].file_id}</code>", parse_mode="HTML")
        elif message.reply_to_message.document:
            await message.answer(f"DOC file_id:\n<code>{message.reply_to_message.document.file_id}</code>", parse_mode="HTML")
        elif message.reply_to_message.audio:
            await message.answer(f"AUDIO file_id:\n<code>{message.reply_to_message.audio.file_id}</code>", parse_mode="HTML")
        elif message.reply_to_message.voice:
            await message.answer(f"VOICE file_id:\n<code>{message.reply_to_message.voice.file_id}</code>", parse_mode="HTML")
        elif message.reply_to_message.video_note:
            await message.answer(f"VIDEO_NOTE file_id:\n<code>{message.reply_to_message.video_note.file_id}</code>", parse_mode="HTML")
        else:
            await message.answer("В этом сообщении нет поддерживаемых медиафайлов.")
    else:
        await message.answer("Ответь на сообщение с файлом")
