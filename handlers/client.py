import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime

from database.db import (
    add_user,
    get_user,
    update_user_agreed,
    update_first_lesson_started,
    update_lesson_clicked,
    get_days_left,
    get_user_payments
)
from keyboards.client_kb import (
    get_oferta_keyboard,
    get_main_menu_keyboard,
    get_tariffs_keyboard,
    get_account_keyboard,
    get_back_to_menu_keyboard
)
from config import REMINDER_DELAY, SAD_CAT_PHOTO

router = Router()

# Словарь для отслеживания активных таймеров
active_timers = {}

async def send_reminder(user_id: int, bot):
    """Отправка напоминания через 10 минут"""
    await asyncio.sleep(REMINDER_DELAY)

    # Проверяем, кликнул ли пользователь по уроку
    user = await get_user(user_id)
    if user and not user['lesson_clicked']:
        # Отправляем фото грустного кота
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=SAD_CAT_PHOTO,
                caption="😿 Ты так и не начал урок...\nНе забудь вернуться к обучению!"
            )
        except Exception as e:
            print(f"Ошибка отправки напоминания: {e}")

    # Удаляем таймер из активных
    if user_id in active_timers:
        del active_timers[user_id]

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id

    # Добавляем пользователя в БД
    await add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    # Проверяем согласие с офертой
    user = await get_user(user_id)

    if not user['agreed']:
        # Показываем оферту
        text = f"""
👋 Привет, {message.from_user.first_name}!

Добро пожаловать в наш бот! 🎓

Для продолжения работы необходимо ознакомиться с документами и принять условия использования.

Нажмите на кнопки ниже для ознакомления с документами 👇
"""
        await message.answer(text, reply_markup=get_oferta_keyboard())
    else:
        # Показываем главное меню
        text = f"""
🏠 Главное меню

Привет, {message.from_user.first_name}! Выбери действие:
"""
        await message.answer(text, reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "agree_oferta")
async def agree_oferta(callback: CallbackQuery):
    """Согласие с офертой"""
    user_id = callback.from_user.id

    # Обновляем статус согласия
    await update_user_agreed(user_id, True)

    text = f"""
✅ Спасибо за согласие!

🏠 Главное меню

Добро пожаловать! Выбери действие:
"""
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer("Вы успешно приняли условия!")

@router.callback_query(F.data == "start_lesson")
async def start_lesson(callback: CallbackQuery):
    """Старт урока"""
    user_id = callback.from_user.id

    # Проверяем, первый ли это урок
    user = await get_user(user_id)

    if not user['first_lesson_started']:
        # Отмечаем начало первого урока
        await update_first_lesson_started(user_id)

        # Сбрасываем флаг lesson_clicked
        await update_lesson_clicked(user_id, False)

        # Запускаем таймер напоминания
        if user_id in active_timers:
            active_timers[user_id].cancel()

        task = asyncio.create_task(send_reminder(user_id, callback.bot))
        active_timers[user_id] = task

    text = """
🎓 Урок запущен!

Вот материалы для изучения:

📚 [Ссылка на урок здесь]

Нажми на кнопку ниже, когда приступишь к изучению 👇
"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Приступил к уроку", callback_data="lesson_started_confirm")],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "lesson_started_confirm")
async def lesson_started_confirm(callback: CallbackQuery):
    """Подтверждение начала урока"""
    user_id = callback.from_user.id

    # Отмечаем клик по уроку
    await update_lesson_clicked(user_id, True)

    # Отменяем таймер, если он активен
    if user_id in active_timers:
        active_timers[user_id].cancel()
        del active_timers[user_id]

    text = """
✅ Отлично! Продолжай обучение!

Желаю успехов! 💪
"""
    await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    await callback.answer("Молодец! Продолжай в том же духе!")

@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery):
    """Меню покупки подписки"""
    text = """
💳 Выберите тариф:

Выберите подходящий период подписки 👇
"""
    await callback.message.edit_text(text, reply_markup=get_tariffs_keyboard())
    await callback.answer()

@router.callback_query(F.data == "my_account")
async def my_account(callback: CallbackQuery):
    """Личный кабинет"""
    text = """
👤 Личный кабинет

Выберите действие:
"""
    await callback.message.edit_text(text, reply_markup=get_account_keyboard())
    await callback.answer()

@router.callback_query(F.data == "days_left")
async def days_left_handler(callback: CallbackQuery):
    """Показать оставшиеся дни подписки"""
    user_id = callback.from_user.id
    days = await get_days_left(user_id)

    if days > 0:
        text = f"""
📅 Дней осталось: {days}

Ваша подписка активна до: {(datetime.now().date()).isoformat()} + {days} дней
"""
        if days <= 7:
            text += "\n⚠️ Не забудьте продлить подписку!"
    else:
        text = """
❌ У вас нет активной подписки

Оформите подписку, чтобы получить доступ к курсу!
"""

    await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "payment_history")
async def payment_history_handler(callback: CallbackQuery):
    """История платежей"""
    user_id = callback.from_user.id
    payments = await get_user_payments(user_id)

    if payments:
        text = "💰 История платежей:\n\n"
        for payment in payments:
            date = datetime.fromisoformat(payment['date']).strftime("%d.%m.%Y %H:%M")
            text += f"• {date} - {payment['amount']} ₽ ({payment['tariff']} дней)\n"
    else:
        text = """
📝 У вас пока нет платежей

Оформите подписку, чтобы начать обучение!
"""

    await callback.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    text = """
🏠 Главное меню

Выберите действие:
"""
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()
