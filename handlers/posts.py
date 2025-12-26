from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.gemini import generate_post
from keyboards.admin_kb import get_post_confirm_menu
from database.db import add_scheduled_post
from handlers.settings import is_admin, get_current_admin_id, get_current_channel_id
from datetime import datetime, timedelta

router = Router()

class PostStates(StatesGroup):
    waiting_post_text = State()
    waiting_post_topic = State()
    waiting_scheduled_time = State()
    editing_post = State()

# Временное хранилище для текущего поста
temp_post_storage = {}

@router.callback_query(F.data == "auto_post")
async def auto_post_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания автопоста через AI"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = """
🤖 **Автоматическая генерация поста**

Введите тему поста или отправьте /skip для случайной темы:

Примеры тем:
• Мотивация на тренировки
• Польза йоги
• Здоровое питание
• Техника выполнения упражнений
"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PostStates.waiting_post_topic)
    await callback.answer()

@router.message(PostStates.waiting_post_topic)
async def process_post_topic(message: Message, state: FSMContext):
    """Обработка темы и генерация поста"""
    if not is_admin(message.from_user.id):
        return
    
    topic = None if message.text == "/skip" else message.text
    
    await message.answer("⏳ Генерирую пост через AI...")
    
    # Генерируем пост через Gemini
    post_text = await generate_post(topic)
    
    # Сохраняем во временное хранилище
    admin_id = get_current_admin_id()
    temp_post_storage[admin_id] = post_text
    
    # Показываем результат
    preview = f"📝 **Сгенерированный пост:**\n\n{post_text}\n\n" \
              f"Выберите действие:"
    
    await message.answer(preview, reply_markup=get_post_confirm_menu(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "publish_post")
async def publish_post_now(callback: CallbackQuery, bot: Bot):
    """Опубликовать пост немедленно"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    admin_id = get_current_admin_id()
    post_text = temp_post_storage.get(admin_id)
    
    if not post_text:
        await callback.answer("❌ Ошибка: пост не найден")
        return
    
    try:
        # Публикуем в канал
        channel_id = get_current_channel_id()
        await bot.send_message(
            chat_id=channel_id,
            text=post_text,
            parse_mode="Markdown"
        )
        
        # Удаляем из временного хранилища
        temp_post_storage.pop(admin_id, None)
        
        await callback.message.edit_text(
            f"✅ **Пост опубликован!**\n\n{post_text}",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Пост успешно опубликован!")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка публикации: {e}")

@router.callback_query(F.data == "edit_post")
async def edit_post_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = "✏️ Отправьте новый текст поста:"
    await callback.message.edit_text(text)
    await state.set_state(PostStates.editing_post)
    await callback.answer()

@router.message(PostStates.editing_post)
async def process_edited_post(message: Message, state: FSMContext):
    """Обработка отредактированного поста"""
    if not is_admin(message.from_user.id):
        return
    
    # Сохраняем отредактированный текст
    admin_id = get_current_admin_id()
    temp_post_storage[admin_id] = message.text
    
    preview = f"📝 **Отредактированный пост:**\n\n{message.text}\n\n" \
              f"Выберите действие:"
    
    await message.answer(preview, reply_markup=get_post_confirm_menu(), parse_mode="Markdown")
    await state.clear()

@router.callback_query(F.data == "scheduled_post")
async def scheduled_post_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания отложенного поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    text = """
⏰ **Отложенный пост**

Напишите текст поста:
"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PostStates.waiting_post_text)
    await callback.answer()

@router.message(PostStates.waiting_post_text)
async def process_scheduled_text(message: Message, state: FSMContext):
    """Обработка текста отложенного поста"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(post_text=message.text)
    
    text = """
⏰ Когда опубликовать пост?

Отправьте время в формате:
`ДД.ММ.ГГГГ ЧЧ:ММ`

Например: `25.12.2024 15:30`
"""
    
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(PostStates.waiting_scheduled_time)

@router.message(PostStates.waiting_scheduled_time)
async def process_scheduled_time(message: Message, state: FSMContext):
    """Обработка времени публикации"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # Парсим дату и время
        publish_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        
        # Проверяем, что время в будущем
        if publish_time <= datetime.now():
            await message.answer("❌ Время должно быть в будущем!")
            return
        
        # Получаем текст поста
        data = await state.get_data()
        post_text = data.get('post_text')
        
        # Сохраняем в БД
        await add_scheduled_post(
            content=post_text,
            publish_time=publish_time
        )
        
        await message.answer(
            f"✅ **Пост запланирован!**\n\n"
            f"Публикация: {publish_time.strftime('%d.%m.%Y в %H:%M')}\n\n"
            f"Текст:\n{post_text}",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
            "Например: `25.12.2024 15:30`",
            parse_mode="Markdown"
        )
