from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.db import add_payment, get_user
from keyboards.admin_kb import get_payment_confirmation
from config import SUBSCRIPTION_PRICES
from handlers.client import ClientStates
from handlers.settings import get_current_admin_id

router = Router()

@router.message(ClientStates.waiting_payment_photo, F.photo)
async def process_payment_photo(message: Message, state: FSMContext, bot: Bot):
    """Обработка фото чека"""
    data = await state.get_data()
    sub_type = data.get('subscription_type')
    
    # Получаем ID фото (самое большое качество)
    photo_id = message.photo[-1].file_id
    
    # Сумма подписки
    amount = SUBSCRIPTION_PRICES[sub_type]
    
    # Сохраняем платеж в БД
    payment_id = await add_payment(
        user_id=message.from_user.id,
        amount=amount,
        subscription_type=sub_type,
        photo_id=photo_id
    )
    
    # Получаем данные пользователя
    user = await get_user(message.from_user.id)
    
    # Уведомляем админа
    periods = {
        '1_month': '1 месяц',
        '3_months': '3 месяца',
        '6_months': '6 месяцев',
        '12_months': '12 месяцев'
    }
    
    admin_text = f"""
💰 **Новый платеж на проверку!**

От: {message.from_user.first_name} (@{message.from_user.username or 'без username'})
ID: `{message.from_user.id}`

Сумма: {amount}₽
Период: {periods[sub_type]}

Чек прикреплен ниже 👇
"""
    
    admin_id = get_current_admin_id()
    await bot.send_photo(
        chat_id=admin_id,
        photo=photo_id,
        caption=admin_text,
        reply_markup=get_payment_confirmation(payment_id, message.from_user.id),
        parse_mode="Markdown"
    )
    
    # Подтверждаем клиенту
    await message.answer(
        "✅ Чек получен!\n\n"
        "Администратор проверит платеж в течение 24 часов.\n"
        "Вы получите уведомление после проверки. 🔔",
        reply_markup=message.reply_markup
    )
    
    await state.clear()

@router.message(ClientStates.waiting_payment_photo)
async def wrong_payment_format(message: Message):
    """Неправильный формат чека"""
    await message.answer(
        "❌ Пожалуйста, отправьте **фото** чека об оплате.\n\n"
        "Если возникли проблемы - обратитесь в поддержку.",
        parse_mode="Markdown"
    )
