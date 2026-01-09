"""Agreement keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import settings


def agreement_keyboard() -> InlineKeyboardMarkup:
    """
    Create agreement keyboard with document links and agree button.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text=_("📄 Offer"), url=settings.payment.OFFER_DOCUMENT_URL)],
        [InlineKeyboardButton(text=_("🔒 Privacy Policy"), url=settings.payment.PRIVACY_DOCUMENT_URL)],
        [InlineKeyboardButton(text=_("📋 Consent"), url=settings.payment.CONSENT_DOCUMENT_URL)],
        [InlineKeyboardButton(text=_("✅ I Agree"), callback_data="agreement:agree")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
