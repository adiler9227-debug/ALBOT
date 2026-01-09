"""Channel service."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

from bot.core.config import settings


async def add_to_channel(bot: Bot, user_id: int) -> bool:
    """
    Add user to channel (unban if banned).

    Args:
        bot: Bot instance
        user_id: User ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Unban user (in case they were banned before)
        await bot.unban_chat_member(chat_id=settings.payment.CHANNEL_ID, user_id=user_id, only_if_banned=True)
        logger.info(f"User {user_id} unbanned/added to channel {settings.payment.CHANNEL_ID}")
        return True
    except TelegramBadRequest as e:
        logger.error(f"Failed to add user {user_id} to channel: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding user {user_id} to channel: {e}")
        return False


async def remove_from_channel(bot: Bot, user_id: int) -> bool:
    """
    Remove user from channel (ban + unban).

    Args:
        bot: Bot instance
        user_id: User ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ban user
        await bot.ban_chat_member(chat_id=settings.payment.CHANNEL_ID, user_id=user_id)
        logger.info(f"User {user_id} banned from channel {settings.payment.CHANNEL_ID}")

        # Immediately unban (so they can rejoin later)
        await bot.unban_chat_member(chat_id=settings.payment.CHANNEL_ID, user_id=user_id, only_if_banned=True)
        logger.info(f"User {user_id} unbanned from channel {settings.payment.CHANNEL_ID}")
        return True
    except TelegramBadRequest as e:
        logger.error(f"Failed to remove user {user_id} from channel: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error removing user {user_id} from channel: {e}")
        return False


async def check_channel_membership(bot: Bot, user_id: int) -> bool:
    """
    Check if user is member of channel.

    Args:
        bot: Bot instance
        user_id: User ID

    Returns:
        True if user is member, False otherwise
    """
    try:
        member = await bot.get_chat_member(chat_id=settings.payment.CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id}: {e}")
        return False
