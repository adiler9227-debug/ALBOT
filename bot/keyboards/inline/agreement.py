"""Agreement keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.config import settings


def agreement_keyboard() -> InlineKeyboardMarkup:
    """
    Create agreement keyboard with document links and agree button.

    Returns:
        InlineKeyboardMarkup
    """
    buttons = [
        [InlineKeyboardButton(text="📄 Offer", url=settings.payment.OFFER_DOCUMENT_URL)],
        [InlineKeyboardButton(text="🔒 Privacy Policy", url=settings.payment.PRIVACY_DOCUMENT_URL)],
        [InlineKeyboardButton(text="📋 Consent", url=settings.payment.CONSENT_DOCUMENT_URL)],
        [InlineKeyboardButton(text="✅ I Agree", callback_data="agreement:agree")],
    ]

    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
