from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, Message, LabeledPrice
from datetime import datetime

from database.db import add_payment, update_expiry_date
from config import PAYMENT_TOKEN, TARIFFS
from keyboards.client_kb import get_back_to_menu_keyboard

router = Router()

@router.callback_query(F.data.startswith("tariff_"))
async def process_tariff_selection(callback: CallbackQuery):
    """Обработка выбора тарифа"""
    tariff_id = callback.data.replace("tariff_", "")
    tariff = TARIFFS[tariff_id]

    # Создаем invoice
    await callback.message.answer_invoice(
        title=tariff['title'],
        description=tariff['description'],
        payload=f"tariff_{tariff_id}",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label=tariff['title'], amount=tariff['price'] * 100)  # в копейках
        ],
        start_parameter=f"subscription-{tariff_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )

    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Обработка pre_checkout запроса"""
    # Всегда подтверждаем (можно добавить проверки)
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Обработка успешного платежа"""
    payment_info = message.successful_payment
    user_id = message.from_user.id

    # Получаем ID тарифа из payload
    payload = payment_info.invoice_payload
    tariff_id = payload.replace("tariff_", "")

    tariff = TARIFFS[tariff_id]

    # Записываем платеж в БД
    await add_payment(
        user_id=user_id,
        amount=tariff['price'],
        tariff=tariff['title']
    )

    # Обновляем дату окончания подписки
    await update_expiry_date(user_id, tariff['days'])

    # Отправляем подтверждение
    text = f"""
✅ Оплата успешно прошла!

💳 Сумма: {tariff['price']} ₽
📅 Период: {tariff['title']}

Ваша подписка активирована! 🎉

Приятного обучения! 🎓
"""

    await message.answer(text, reply_markup=get_back_to_menu_keyboard())
