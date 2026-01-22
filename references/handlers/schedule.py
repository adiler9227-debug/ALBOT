from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.gemini import generate_schedule
from keyboards.admin_kb import get_schedule_type_menu, get_schedule_action_menu
from database.db import save_schedule
from handlers.settings import is_admin, get_current_admin_id
from datetime import datetime, timedelta

router = Router()

class ScheduleStates(StatesGroup):
    waiting_manual_schedule = State()
    editing_schedule = State()

# Временное хранилище для расписаний
temp_schedule_storage = {}

@router.callback_query(F.data == "create_schedule")
async def create_schedule_start(callback: CallbackQuery):
    """Начало создания расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = "📋 **Создание расписания**\n\nВыберите период:"
    await callback.message.edit_text(text, reply_markup=get_schedule_type_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("create_"))
async def generate_schedule_ai(callback: CallbackQuery):
    """Генерация расписания через AI"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    schedule_type = callback.data.replace("create_", "")
    
    # Определяем дату начала
    if schedule_type == "day":
        date = datetime.now().strftime("%Y-%m-%d")
        period_text = "на сегодня"
    elif schedule_type == "week":
        date = datetime.now().strftime("%Y-%m-%d")
        period_text = "на неделю"
    else:  # month
        date = datetime.now().strftime("%Y-%m-%d")
        period_text = "на месяц"
    
    await callback.message.edit_text(
        f"⏳ Генерирую расписание {period_text} через AI...",
        parse_mode="Markdown"
    )
    
    # Генерируем через Gemini
    schedule_content = await generate_schedule(schedule_type, date)
    
    # Сохраняем во временное хранилище
    admin_id = get_current_admin_id()
    temp_schedule_storage[admin_id] = {
        'type': schedule_type,
        'date': date,
        'content': schedule_content
    }
    
    # Показываем результат
    preview = f"📋 **Сгенерированное расписание {period_text}:**\n\n{schedule_content}\n\n" \
              f"Выберите действие:"
    
    await callback.message.edit_text(
        preview,
        reply_markup=get_schedule_action_menu(schedule_type),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("save_schedule_"))
async def save_generated_schedule(callback: CallbackQuery):
    """Сохранить сгенерированное расписание"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    admin_id = get_current_admin_id()
    schedule_data = temp_schedule_storage.get(admin_id)
    
    if not schedule_data:
        await callback.answer("❌ Расписание не найдено")
        return
    
    # Сохраняем в БД
    await save_schedule(
        schedule_type=schedule_data['type'],
        date=schedule_data['date'],
        content=schedule_data['content']
    )
    
    # Удаляем из временного хранилища
    temp_schedule_storage.pop(admin_id, None)
    
    period_map = {
        'day': 'на день',
        'week': 'на неделю',
        'month': 'на месяц'
    }
    
    await callback.message.edit_text(
        f"✅ **Расписание {period_map[schedule_data['type']]} сохранено!**\n\n"
        f"Пользователи могут просмотреть его в боте.",
        parse_mode="Markdown"
    )
    await callback.answer("✅ Расписание сохранено!")

@router.callback_query(F.data.startswith("regen_schedule_"))
async def regenerate_schedule(callback: CallbackQuery):
    """Перегенерировать расписание"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    schedule_type = callback.data.replace("regen_schedule_", "")
    
    date = datetime.now().strftime("%Y-%m-%d")
    
    await callback.message.edit_text("⏳ Перегенерирую расписание...")
    
    # Генерируем заново
    schedule_content = await generate_schedule(schedule_type, date)
    
    # Обновляем хранилище
    admin_id = get_current_admin_id()
    temp_schedule_storage[admin_id] = {
        'type': schedule_type,
        'date': date,
        'content': schedule_content
    }
    
    period_map = {
        'day': 'на сегодня',
        'week': 'на неделю',
        'month': 'на месяц'
    }
    
    preview = f"📋 **Обновленное расписание {period_map[schedule_type]}:**\n\n{schedule_content}\n\n" \
              f"Выберите действие:"
    
    await callback.message.edit_text(
        preview,
        reply_markup=get_schedule_action_menu(schedule_type),
        parse_mode="Markdown"
    )
    await callback.answer("🔄 Расписание обновлено!")

@router.callback_query(F.data.startswith("edit_manual_"))
async def edit_schedule_manual(callback: CallbackQuery, state: FSMContext):
    """Ручное редактирование расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    schedule_type = callback.data.replace("edit_manual_", "")
    
    text = "✏️ **Редактирование расписания**\n\nОтправьте новый текст расписания:"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.update_data(schedule_type=schedule_type)
    await state.set_state(ScheduleStates.editing_schedule)
    await callback.answer()

@router.message(ScheduleStates.editing_schedule)
async def process_manual_schedule(message: Message, state: FSMContext):
    """Обработка вручную введенного расписания"""
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    schedule_type = data.get('schedule_type')
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Обновляем хранилище
    admin_id = get_current_admin_id()
    temp_schedule_storage[admin_id] = {
        'type': schedule_type,
        'date': date,
        'content': message.text
    }
    
    period_map = {
        'day': 'на день',
        'week': 'на неделю',
        'month': 'на месяц'
    }
    
    preview = f"📋 **Отредактированное расписание {period_map[schedule_type]}:**\n\n{message.text}\n\n" \
              f"Выберите действие:"
    
    await message.answer(
        preview,
        reply_markup=get_schedule_action_menu(schedule_type),
        parse_mode="Markdown"
    )
    await state.clear()

@router.callback_query(F.data == "edit_schedule")
async def edit_existing_schedule(callback: CallbackQuery):
    """Редактирование существующего расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = """
✏️ **Изменение расписания**

Выберите период для редактирования:
"""
    
    await callback.message.edit_text(text, reply_markup=get_schedule_type_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "view_schedule")
async def view_all_schedules(callback: CallbackQuery):
    """Просмотр всех расписаний"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    from database.db import get_schedule
    
    schedules = await get_schedule()
    
    if not schedules:
        text = "📭 Расписания пока нет"
    else:
        text = "📋 **Все расписания:**\n\n"
        for schedule in schedules:
            type_map = {
                'day': 'День',
                'week': 'Неделя',
                'month': 'Месяц'
            }
            text += f"**{type_map.get(schedule['schedule_type'], 'Неизвестно')}** ({schedule['date']}):\n"
            text += f"{schedule['content'][:100]}...\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()
