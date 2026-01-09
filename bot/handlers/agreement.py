"""Agreement handler."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import main_keyboard
from bot.services import set_agreement

router = Router(name="agreement")


@router.callback_query(F.data == "agreement:agree")
async def agreement_agree_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Handle agreement acceptance.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    # Set agreement in database
    await set_agreement(session, callback.from_user.id)

    # Show welcome message with main menu
    welcome_text = _(
        "✅ Thank you for accepting!\n\n"
        "👋 Welcome, {name}!\n\n"
        "Welcome to the world of breathing practices and Kundalini yoga 🧘‍♀️\n\n"
        "This bot is your guide and helper, with which you will:\n\n"
        "• Learn to cope with anxiety and stress\n"
        "• Get rid of chronic fatigue and apathy\n"
        "• Get rid of swelling and excess weight\n"
        "• Become more energetic and confident\n"
        "• Improve sleep and general well-being\n"
        "• Increase libido and sexuality\n"
        "• Improve memory and cognitive functions\n"
        "• Get rid of addictions\n"
        "• Strengthen your inner support\n\n"
        "Let's start small 👇"
    ).format(name=callback.from_user.first_name)

    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=main_keyboard(),
    )
    await callback.answer(_("Agreement accepted"))
