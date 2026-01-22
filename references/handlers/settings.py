from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
import os

router = Router()

# Файл для хранения настроек
SETTINGS_FILE = 'settings.json'

class SettingsStates(StatesGroup):
    waiting_channel_id = State()
    waiting_admin_id = State()

def load_settings():
    """Загрузить настройки из файла"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'channel_id': -1003574169604,
        'admin_id': 7737327242
    }

def save_settings(settings):
    """Сохранить настройки в файл"""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_current_admin_id():
    """Получить текущий ID админа"""
    settings = load_settings()
    return settings.get('admin_id', 7737327242)

def get_current_channel_id():
    """Получить текущий ID канала"""
    settings = load_settings()
    return settings.get('channel_id', -1003574169604)

def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == get_current_admin_id()

def get_settings_menu():
    """Меню настроек"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Изменить ID админа", callback_data="change_admin")],
            [InlineKeyboardButton(text="📢 Изменить ID канала", callback_data="change_channel")],
            [InlineKeyboardButton(text="👁 Показать настройки", callback_data="view_settings")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ]
    )
    return keyboard

@router.message(Command("settings"))
async def settings_command(message: Message):
    """Команда для настроек"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к настройкам")
        return
    
    text = """
⚙️ **Настройки бота**

Здесь вы можете изменить:
• ID администратора
• ID канала для постов

Выберите действие:
"""
    
    await message.answer(text, reply_markup=get_settings_menu(), parse_mode="Markdown")

@router.callback_query(F.data == "view_settings")
async def view_current_settings(callback: CallbackQuery):
    """Показать текущие настройки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    settings = load_settings()
    
    text = f"""
👁 **Текущие настройки:**

👤 ID Админа: `{settings['admin_id']}`
📢 ID Канала: `{settings['channel_id']}`

Для изменения выберите нужный пункт выше.
"""
    
    await callback.message.edit_text(text, reply_markup=get_settings_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "change_admin")
async def change_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение ID админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = """
👤 **Изменение ID админа**

Отправьте новый ID администратора.

Как узнать ID:
1. Напишите боту @userinfobot
2. Скопируйте ваш ID
3. Отправьте сюда

❗️ Будьте внимательны! После изменения доступ к настройкам получит только новый админ.
"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(SettingsStates.waiting_admin_id)
    await callback.answer()

@router.message(SettingsStates.waiting_admin_id)
async def process_new_admin_id(message: Message, state: FSMContext):
    """Обработка нового ID админа"""
    try:
        new_admin_id = int(message.text.strip())
        
        # Сохраняем настройки
        settings = load_settings()
        old_admin_id = settings['admin_id']
        settings['admin_id'] = new_admin_id
        save_settings(settings)
        
        await message.answer(
            f"✅ **ID админа изменен!**\n\n"
            f"Старый: `{old_admin_id}`\n"
            f"Новый: `{new_admin_id}`",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "ID должен быть числом, например: `7737327242`",
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "change_channel")
async def change_channel_start(callback: CallbackQuery, state: FSMContext):
    """Начать изменение ID канала"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = """
📢 **Изменение ID канала**

Отправьте новый ID канала/группы.

Как узнать ID канала:
1. Добавьте бота @userinfobot в канал как админа
2. Перешлите любое сообщение из канала боту
3. Он пришлет ID канала (например: `-1001234567890`)
4. Скопируйте и отправьте сюда

⚠️ Не забудьте добавить бота в новый канал как админа с правами на публикацию!
"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(SettingsStates.waiting_channel_id)
    await callback.answer()

@router.message(SettingsStates.waiting_channel_id)
async def process_new_channel_id(message: Message, state: FSMContext):
    """Обработка нового ID канала"""
    try:
        new_channel_id = int(message.text.strip())
        
        # Проверяем, что ID начинается с -100 (формат супергруппы/канала)
        if not str(new_channel_id).startswith('-100'):
            await message.answer(
                "⚠️ **Внимание!**\n\n"
                "ID канала обычно начинается с `-100`\n"
                "Убедитесь, что вы ввели правильный ID.\n\n"
                "Продолжить? Отправьте ID еще раз для подтверждения."
            )
            return
        
        # Сохраняем настройки
        settings = load_settings()
        old_channel_id = settings['channel_id']
        settings['channel_id'] = new_channel_id
        save_settings(settings)
        
        await message.answer(
            f"✅ **ID канала изменен!**\n\n"
            f"Старый: `{old_channel_id}`\n"
            f"Новый: `{new_channel_id}`\n\n"
            f"⚠️ Убедитесь, что бот добавлен в канал как админ!",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "ID должен быть числом, например: `-1003574169604`",
            parse_mode="Markdown"
        )

# Экспортируем функции для использования в других модулях
__all__ = ['get_current_admin_id', 'get_current_channel_id', 'is_admin', 'load_settings']
