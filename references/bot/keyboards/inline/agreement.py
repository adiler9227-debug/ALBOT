"""Agreement keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def agreement_keyboard() -> InlineKeyboardMarkup:
    """Create agreement keyboard."""
    buttons = [
        [InlineKeyboardButton(text="📄 Оферта", callback_data="agreement:offer")],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="agreement:privacy")],
        [InlineKeyboardButton(text="📋 Согласие на обработку данных", callback_data="agreement:consent")],
        [InlineKeyboardButton(text="✅ Я согласен(а)", callback_data="agreement:agree")],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
