from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OFERTA_URL, PRIVACY_URL, TARIFFS

def get_oferta_keyboard():
    """Клавиатура с документами и кнопкой согласия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Оферта", url=OFERTA_URL)],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", url=PRIVACY_URL)],
        [InlineKeyboardButton(text="✅ Согласен с условиями", callback_data="agree_oferta")]
    ])
    return keyboard

def get_main_menu_keyboard():
    """Главное меню после согласия с офертой"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Старт урока", callback_data="start_lesson")],
        [InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="my_account")],
    ])
    return keyboard

def get_tariffs_keyboard():
    """Клавиатура выбора тарифа"""
    buttons = []
    for tariff_id, tariff_data in TARIFFS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{tariff_data['title']} - {tariff_data['price']} ₽",
                callback_data=f"tariff_{tariff_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_account_keyboard():
    """Клавиатура личного кабинета"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Дней осталось", callback_data="days_left")],
        [InlineKeyboardButton(text="💰 История платежей", callback_data="payment_history")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")],
    ])
    return keyboard

def get_back_to_menu_keyboard():
    """Простая кнопка возврата в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard
