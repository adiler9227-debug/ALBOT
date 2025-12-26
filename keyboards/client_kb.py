from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Главное меню для клиента"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Дней до окончания")],
            [KeyboardButton(text="💳 Продлить доступ")],
            [KeyboardButton(text="📋 Расписание")],
            [KeyboardButton(text="💬 Служба поддержки")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_subscription_menu():
    """Меню выбора подписки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц - 1990₽", callback_data="sub_1_month")],
            [InlineKeyboardButton(text="3 месяца - 4770₽", callback_data="sub_3_months")],
            [InlineKeyboardButton(text="6 месяцев - 8940₽", callback_data="sub_6_months")],
            [InlineKeyboardButton(text="12 месяцев - 15900₽", callback_data="sub_12_months")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard

def get_schedule_menu():
    """Меню выбора периода расписания"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 На сегодня", callback_data="schedule_today")],
            [InlineKeyboardButton(text="📆 На неделю", callback_data="schedule_week")],
            [InlineKeyboardButton(text="🗓 На месяц", callback_data="schedule_month")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ]
    )
    return keyboard

def get_back_button():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
        ]
    )
    return keyboard
