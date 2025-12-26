from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.db import update_payment_status, update_subscription, get_pending_payments, get_user
from keyboards.admin_kb import get_admin_menu, get_posts_menu, get_schedule_admin_menu
from config import SUBSCRIPTION_DAYS
from handlers.settings import is_admin, get_current_admin_id

router = Router()

@router.message(F.text == "💰 Проверить платежи")
async def check_payments(message: Message):
    """Проверка платежей"""
    if not is_admin(message.from_user.id):
        return
    
    payments = await get_pending_payments()
    
    if not payments:
        await message.answer("📭 Нет платежей на проверку")
        return
    
    await message.answer(f"📬 Найдено платежей на проверку: {len(payments)}")

@router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback: CallbackQuery, bot: Bot):
    """Подтверждение платежа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    # Парсим данные
    _, _, payment_id, user_id = callback.data.split("_")
    payment_id = int(payment_id)
    user_id = int(user_id)
    
    # Обновляем статус платежа
    await update_payment_status(payment_id, "approved")
    
    # Получаем данные пользователя из БД
    from database.db import get_user
    async with __import__('aiosqlite').connect('database/subscriptions.db') as db:
        db.row_factory = __import__('aiosqlite').Row
        async with db.execute('SELECT * FROM payments WHERE id = ?', (payment_id,)) as cursor:
            payment = await cursor.fetchone()
    
    if payment:
        # Продлеваем подписку
        days = SUBSCRIPTION_DAYS[payment['subscription_type']]
        await update_subscription(user_id, days)
        
        # Уведомляем пользователя
        user = await get_user(user_id)
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ **Платеж подтвержден!**\n\n"
                 f"Ваша подписка продлена на {days} дней! 🎉\n\n"
                 f"Добро пожаловать в клуб! 💪",
            parse_mode="Markdown"
        )
        
        # Подтверждаем админу
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n✅ **ПОДТВЕРЖДЕНО**",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Платеж подтвержден, подписка продлена!")
    else:
        await callback.answer("❌ Ошибка при обработке платежа")

@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    """Отклонение платежа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    # Парсим данные
    _, _, payment_id, user_id = callback.data.split("_")
    payment_id = int(payment_id)
    user_id = int(user_id)
    
    # Обновляем статус
    await update_payment_status(payment_id, "rejected")
    
    # Уведомляем пользователя
    await bot.send_message(
        chat_id=user_id,
        text="❌ **Платеж отклонен**\n\n"
             "К сожалению, платеж не прошел проверку.\n"
             "Пожалуйста, свяжитесь с администратором для уточнения деталей.",
        parse_mode="Markdown"
    )
    
    # Подтверждаем админу
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ **ОТКЛОНЕНО**",
        parse_mode="Markdown"
    )
    await callback.answer("❌ Платеж отклонен")

@router.message(F.text == "📢 Управление постами")
async def posts_management(message: Message):
    """Управление постами"""
    if not is_admin(message.from_user.id):
        return
    
    text = "📢 **Управление постами**\n\nВыберите действие:"
    await message.answer(text, reply_markup=get_posts_menu(), parse_mode="Markdown")

@router.message(F.text == "📋 Управление расписанием")
async def schedule_management(message: Message):
    """Управление расписанием"""
    if not is_admin(message.from_user.id):
        return
    
    text = "📋 **Управление расписанием**\n\nВыберите действие:"
    await message.answer(text, reply_markup=get_schedule_admin_menu(), parse_mode="Markdown")

@router.message(F.text == "👥 Статистика")
async def show_stats(message: Message):
    """Показать статистику"""
    if not is_admin(message.from_user.id):
        return
    
    # Подсчитываем статистику из БД
    import aiosqlite
    async with aiosqlite.connect('database/subscriptions.db') as db:
        # Всего пользователей
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            total_users = (await cursor.fetchone())[0]
        
        # Активные подписки
        async with db.execute(
            'SELECT COUNT(*) FROM users WHERE subscription_end > datetime("now")'
        ) as cursor:
            active_subs = (await cursor.fetchone())[0]
        
        # Платежи на проверке
        async with db.execute(
            'SELECT COUNT(*) FROM payments WHERE status = "pending"'
        ) as cursor:
            pending_payments = (await cursor.fetchone())[0]
    
    text = f"""
📊 **Статистика**

👥 Всего пользователей: {total_users}
✅ Активных подписок: {active_subs}
⏳ Платежей на проверке: {pending_payments}
"""
    
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в админ меню"""
    text = "🔐 **Админ панель**\n\nВыберите действие:"
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_posts")
async def admin_posts_callback(callback: CallbackQuery):
    """Вернуться к управлению постами"""
    text = "📢 **Управление постами**\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=get_posts_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_schedule")
async def admin_schedule_callback(callback: CallbackQuery):
    """Вернуться к управлению расписанием"""
    text = "📋 **Управление расписанием**\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=get_schedule_admin_menu(), parse_mode="Markdown")
    await callback.answer()
