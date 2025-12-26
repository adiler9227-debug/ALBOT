from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import add_user, get_days_left, get_schedule
from keyboards.client_kb import get_main_menu, get_subscription_menu, get_schedule_menu, get_back_button
from keyboards.admin_kb import get_admin_menu
from handlers.settings import is_admin
from config import SUBSCRIPTION_PRICES
from datetime import datetime

router = Router()

class ClientStates(StatesGroup):
    waiting_payment_photo = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    await add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Проверяем - админ или клиент
    if is_admin(message.from_user.id):
        # Админ меню
        text = f"""
🔐 **Админ-панель**

Привет, {message.from_user.first_name}!

Выбери действие:
"""
        await message.answer(text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    else:
        # Клиент меню
        welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Добро пожаловать в клуб byAlina! 💪

Здесь ты найдешь:
• Расписание тренировок
• Мотивационные посты
• Поддержку и советы

Выбери действие в меню ниже 👇
"""
        await message.answer(welcome_text, reply_markup=get_main_menu())

@router.message(F.text == "📅 Дней до окончания")
async def check_subscription(message: Message):
    """Проверка оставшихся дней подписки"""
    days_left = await get_days_left(message.from_user.id)
    
    if days_left > 0:
        text = f"⏰ До окончания подписки осталось: **{days_left} дней**"
        if days_left <= 3:
            text += "\n\n⚠️ Не забудь продлить подписку!"
    else:
        text = "❌ У вас нет активной подписки\n\nНажмите 💳 Продлить доступ"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "💳 Продлить доступ")
async def extend_subscription(message: Message):
    """Меню продления подписки"""
    text = """
💳 **Выберите период подписки:**

Чем длиннее период - тем выгоднее! 🎁
"""
    await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора подписки"""
    sub_type = callback.data.replace("sub_", "")
    price = SUBSCRIPTION_PRICES[sub_type]
    
    periods = {
        '1_month': '1 месяц',
        '3_months': '3 месяца',
        '6_months': '6 месяцев',
        '12_months': '12 месяцев'
    }
    
    text = f"""
📝 **Оформление подписки**

Период: {periods[sub_type]}
Стоимость: {price}₽

💰 **Реквизиты для оплаты:**
Карта: `2202 2063 7495 0660`

После оплаты пришлите скриншот чека 📸
"""
    
    await state.update_data(subscription_type=sub_type)
    await state.set_state(ClientStates.waiting_payment_photo)
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "📋 Расписание")
async def show_schedule_menu(message: Message):
    """Показать меню расписания"""
    text = "📋 **Выберите период:**"
    await message.answer(text, reply_markup=get_schedule_menu(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("schedule_"))
async def show_schedule(callback: CallbackQuery):
    """Показать расписание"""
    schedule_type = callback.data.replace("schedule_", "")
    
    # Определяем дату
    today = datetime.now().strftime("%Y-%m-%d")
    
    type_map = {
        'today': 'day',
        'week': 'week',
        'month': 'month'
    }
    
    schedule = await get_schedule(today)
    
    if schedule:
        text = f"📋 **Расписание:**\n\n{schedule['content']}"
    else:
        text = "📋 Расписание еще не готово.\nАдминистратор скоро его добавит! ⏳"
    
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "💬 Служба поддержки")
async def support(message: Message):
    """Связь с поддержкой"""
    from handlers.settings import get_current_admin_id
    
    admin_id = get_current_admin_id()
    
    text = f"""
💬 **Служба поддержки**

По всем вопросам обращайтесь к администратору:
👉 [Написать админу](tg://user?id={admin_id})

Обычно отвечаем в течение 24 часов ⏰
"""
    
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    text = "🏠 Главное меню"
    await callback.message.edit_text(text)
    await callback.message.answer("Выберите действие:", reply_markup=get_main_menu())
    await callback.answer()
