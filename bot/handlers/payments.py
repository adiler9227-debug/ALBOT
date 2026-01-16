"""Payment handlers."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.keyboards.inline import back_to_main_keyboard, tariffs_keyboard
from bot.services import mark_lesson_clicked
from bot.services.prodamus import apply_promocode, create_payment, generate_payment_url

router = Router(name="payments")


# Payment states
class PaymentStates(StatesGroup):
    """Payment flow states."""

    waiting_for_promocode = State()


# Tariff configuration
TARIFFS = {
    "7": {
        "days": settings.payment.TARIFF_7_DAYS,
        "price": settings.payment.TARIFF_7_PRICE,
        "title": "Пробная неделя",
        "description": "Доступ к занятиям на 7 дней",
    },
    "30": {
        "days": settings.payment.TARIFF_30_DAYS,
        "price": settings.payment.TARIFF_30_PRICE,
        "title": "1 месяц",
        "description": "Доступ к занятиям на 30 дней",
    },
    "90": {
        "days": settings.payment.TARIFF_90_DAYS,
        "price": settings.payment.TARIFF_90_PRICE,
        "title": "3 месяца",
        "description": "Доступ к занятиям на 90 дней",
    },
    "180": {
        "days": settings.payment.TARIFF_180_DAYS,
        "price": settings.payment.TARIFF_180_PRICE,
        "title": "Полгода",
        "description": "Доступ к занятиям на 180 дней",
    },
    "365": {
        "days": settings.payment.TARIFF_365_DAYS,
        "price": settings.payment.TARIFF_365_PRICE,
        "title": "1 год",
        "description": "Доступ к занятиям на 365 дней",
    },
}


@router.callback_query(F.data == "buy_subscription")
async def show_tariffs_handler(callback: CallbackQuery) -> None:
    """
    Show available tariffs.

    Args:
        callback: Callback query
    """
    if not callback.message:
        return

    text = (
        "💎 <b>Выберите тариф:</b>\n\n"
        f"🌱 {TARIFFS['7']['title']} — {TARIFFS['7']['price']} ₽\n"
        f"📅 {TARIFFS['30']['title']} — {TARIFFS['30']['price']} ₽\n"
        f"📆 {TARIFFS['90']['title']} — {TARIFFS['90']['price']} ₽ <i>(-20%)</i>\n"
        f"🌟 {TARIFFS['180']['title']} — {TARIFFS['180']['price']} ₽ <i>(-25%)</i>\n"
        f"⭐ {TARIFFS['365']['title']} — {TARIFFS['365']['price']} ₽ <i>(-35%)</i>\n\n"
        "У вас есть промокод? Введите его на следующем шаге! 🎁"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=tariffs_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def tariff_selection_handler(
    callback: CallbackQuery,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Handle tariff selection and ask for promocode.

    Args:
        callback: Callback query
        bot: Bot instance
        session: Database session
        state: FSM context
    """
    if not callback.from_user or not callback.message:
        return

    # Mark lesson as clicked (user is interested)
    await mark_lesson_clicked(session, callback.from_user.id)

    # Get tariff ID
    tariff_id = callback.data.split(":")[1]
    if tariff_id not in TARIFFS:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    tariff = TARIFFS[tariff_id]

    # Save tariff to state
    await state.update_data(tariff_id=tariff_id)
    await state.set_state(PaymentStates.waiting_for_promocode)

    # Ask for promocode
    text = (
        f"📦 <b>{tariff['title']}</b>\n"
        f"💰 Стоимость: {tariff['price']} ₽\n"
        f"📅 Срок: {tariff['days']} дней\n\n"
        "🎁 Есть промокод? Отправьте его следующим сообщением.\n"
        "Если промокода нет, отправьте любое сообщение или нажмите /skip"
    )

    await callback.message.edit_text(text)
    await callback.answer()


@router.message(PaymentStates.waiting_for_promocode)
@router.message(F.text, F.text.startswith("/skip"))
async def process_promocode_and_payment(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Process promocode and generate payment link.

    Args:
        message: User message with promocode
        bot: Bot instance
        session: Database session
        state: FSM context
    """
    if not message.from_user or not message.text:
        return

    # Get tariff from state
    data = await state.get_data()
    tariff_id = data.get("tariff_id")

    if not tariff_id or tariff_id not in TARIFFS:
        await message.answer("Ошибка: тариф не выбран. Начните заново с /start")
        await state.clear()
        return

    tariff = TARIFFS[tariff_id]
    user_id = message.from_user.id
    base_price = tariff["price"]

    # Check if user wants to skip promocode
    skip_promocode = message.text.lower() in ["/skip", "пропустить", "нет", "skip"]

    # Try to apply promocode
    final_price = base_price
    promocode_model = None
    promocode_text = ""

    if not skip_promocode:
        promocode = message.text.strip().upper()
        final_price, promocode_model = await apply_promocode(
            session, user_id, promocode, base_price
        )

        if promocode_model:
            discount = base_price - final_price
            promocode_text = f"\n🎉 Промокод применен! Скидка: {discount} ₽"
        else:
            promocode_text = "\n⚠️ Промокод не найден или уже использован"

    # Create pending payment record
    order_id = f"user_{user_id}_days_{tariff['days']}"

    await create_payment(
        session=session,
        user_id=user_id,
        amount=final_price,
        subscription_days=tariff["days"],
        payment_id=order_id,
        status="pending",
    )

    # Record promocode usage if applied
    if promocode_model:
        from bot.services.prodamus import record_promocode_usage
        await record_promocode_usage(session, user_id, promocode_model)

    # Generate payment URL
    payment_url = generate_payment_url(
        order_id=order_id,
        amount=final_price,
        products=f"{tariff['title']} - {tariff['days']} дней",
    )

    # Send payment link
    text = (
        f"💳 <b>Оплата подписки</b>\n\n"
        f"📦 Тариф: {tariff['title']}\n"
        f"📅 Срок: {tariff['days']} дней\n"
        f"💰 К оплате: <b>{final_price} ₽</b>"
        f"{promocode_text}\n\n"
        f"👇 Нажмите на кнопку ниже для оплаты:\n"
        f'<a href="{payment_url}">💳 Оплатить {final_price} ₽</a>\n\n'
        f"После оплаты вы автоматически получите доступ к каналу! 🎉"
    )

    await message.answer(text, reply_markup=back_to_main_keyboard())

    # Clear state
    await state.clear()

    logger.info(
        f"Generated payment link for user {user_id}: "
        f"{tariff['days']} days, {final_price} RUB"
    )
