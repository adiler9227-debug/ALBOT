from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu():
    """Главное меню для админа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Проверить платежи")],
            [KeyboardButton(text="📢 Управление постами")],
            [KeyboardButton(text="📋 Управление расписанием")],
            [KeyboardButton(text="👥 Статистика")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_payment_confirmation(payment_id: int, user_id: int):
    """Клавиатура подтверждения платежа"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_payment_{payment_id}_{user_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payment_{payment_id}_{user_id}")
            ]
        ]
    )
    return keyboard

def get_posts_menu():
    """Меню управления постами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Автопост (AI)", callback_data="auto_post")],
            [InlineKeyboardButton(text="⏰ Отложенный пост", callback_data="scheduled_post")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ]
    )
    return keyboard

def get_schedule_admin_menu():
    """Меню управления расписанием для админа"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать расписание", callback_data="create_schedule")],
            [InlineKeyboardButton(text="✏️ Изменить расписание", callback_data="edit_schedule")],
            [InlineKeyboardButton(text="👁 Просмотр расписания", callback_data="view_schedule")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ]
    )
    return keyboard

def get_schedule_type_menu():
    """Выбор типа расписания"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 На день", callback_data="create_day")],
            [InlineKeyboardButton(text="📆 На неделю", callback_data="create_week")],
            [InlineKeyboardButton(text="🗓 На месяц", callback_data="create_month")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_schedule")]
        ]
    )
    return keyboard

def get_schedule_action_menu(schedule_type: str):
    """Меню действий с расписанием после генерации"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data=f"save_schedule_{schedule_type}")],
            [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data=f"regen_schedule_{schedule_type}")],
            [InlineKeyboardButton(text="✏️ Редактировать вручную", callback_data=f"edit_manual_{schedule_type}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_schedule")]
        ]
    )
    return keyboard

def get_post_confirm_menu():
    """Подтверждение публикации поста"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_post")],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_post")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_posts")]
        ]
    )
    return keyboard
