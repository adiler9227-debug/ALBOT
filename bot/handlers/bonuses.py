"""Bonuses and referral handlers."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database.models import PromocodeModel, ReferralModel, VideoReviewModel
from bot.keyboards.inline import back_to_main_keyboard

router = Router(name="bonuses")


# States for video review
class VideoReviewStates(StatesGroup):
    """Video review flow states."""

    waiting_for_video = State()


@router.callback_query(F.data == "bonuses")
async def show_bonuses_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Show bonuses menu with referral and video review options.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.message or not callback.from_user:
        return

    user_id = callback.from_user.id

    # Count referrals
    query = select(ReferralModel).filter_by(referrer_id=user_id)
    result = await session.execute(query)
    referrals = result.scalars().all()
    total_referrals = len(referrals)
    successful_referrals = sum(1 for r in referrals if r.is_bonus_given)

    # Check if user has uploaded video review
    video_query = select(VideoReviewModel).filter_by(user_id=user_id)
    video_result = await session.execute(video_query)
    video_review = video_result.scalar_one_or_none()
    has_video_review = video_review is not None

    text = (
        "🎁 <b>Бонусы и подарки</b>\n\n"
        f"👥 <b>Приведи друга:</b>\n"
        f"├ Всего приглашений: {total_referrals}\n"
        f"├ Оплатили подписку: {successful_referrals}\n"
        f"└ Бонус: +{settings.payment.REFERRAL_BONUS_DAYS} дней за каждого друга\n\n"
        f"🎥 <b>Видео-отзыв:</b>\n"
    )

    if has_video_review:
        text += f"└ ✅ Видео-отзыв отправлен! Промокод активирован на {settings.payment.VIDEO_REVIEW_DISCOUNT} ₽\n\n"
    else:
        text += (
            f"└ 📹 Отправьте видео-отзыв и получите промокод на {settings.payment.VIDEO_REVIEW_DISCOUNT} ₽!\n\n"
        )

    text += (
        "<b>Как получить бонусы:</b>\n\n"
        "1️⃣ <b>Пригласи друга</b> — нажми кнопку ниже, получи реферальную ссылку\n"
        "   Когда друг оплатит подписку, ты получишь +30 дней в подарок!\n\n"
        "2️⃣ <b>Видео-отзыв</b> — запиши короткое видео о своих впечатлениях\n"
        f"   Получи промокод на скидку {settings.payment.VIDEO_REVIEW_DISCOUNT} ₽!"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👥 Пригласить друга", callback_data="get_referral_link"))

    if not has_video_review:
        builder.row(InlineKeyboardButton(text="🎥 Отправить видео-отзыв", callback_data="upload_video_review"))

    builder.row(InlineKeyboardButton(text="« Назад", callback_data="menu:main"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "get_referral_link")
async def get_referral_link_handler(callback: CallbackQuery, bot: Bot) -> None:
    """
    Generate and send referral link.

    Args:
        callback: Callback query
        bot: Bot instance
    """
    if not callback.message or not callback.from_user:
        return

    # Get bot info
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    referral_code = f"ref_{callback.from_user.id}"
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

    text = (
        "👥 <b>Твоя реферальная ссылка:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        "📱 Поделись этой ссылкой с друзьями!\n\n"
        f"🎁 За каждого друга, который оплатит подписку, "
        f"ты получишь <b>+{settings.payment.REFERRAL_BONUS_DAYS} дней</b> в подарок!\n\n"
        "<i>Просто отправь ссылку друзьям или размести в социальных сетях</i>"
    )

    await callback.message.edit_text(text, reply_markup=back_to_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "upload_video_review")
async def start_video_review_upload(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Start video review upload process.

    Args:
        callback: Callback query
        state: FSM context
    """
    if not callback.message:
        return

    await state.set_state(VideoReviewStates.waiting_for_video)

    text = (
        "🎥 <b>Отправьте видео-отзыв</b>\n\n"
        "📹 Запишите короткое видео (до 3 минут) о:\n"
        "├ Ваших впечатлениях от занятий\n"
        "├ Какие результаты вы заметили\n"
        "└ Что вам больше всего нравится\n\n"
        "📤 Отправьте видео следующим сообщением\n\n"
        f"🎁 После отправки вы получите промокод <b>VIDEOOTZIV</b> "
        f"на скидку {settings.payment.VIDEO_REVIEW_DISCOUNT} ₽!"
    )

    await callback.message.edit_text(text)
    await callback.answer()


@router.message(VideoReviewStates.waiting_for_video, F.video)
async def process_video_review(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """
    Process uploaded video review.

    Args:
        message: Message with video
        bot: Bot instance
        session: Database session
        state: FSM context
    """
    if not message.from_user or not message.video:
        return

    user_id = message.from_user.id

    # Check if user already uploaded video review
    existing_query = select(VideoReviewModel).filter_by(user_id=user_id)
    existing_result = await session.execute(existing_query)
    if existing_result.scalar_one_or_none():
        await message.answer(
            "⚠️ Вы уже отправляли видео-отзыв и получили промокод!",
            reply_markup=back_to_main_keyboard(),
        )
        await state.clear()
        return

    # Get or create VIDEOOTZIV promocode
    promo_query = select(PromocodeModel).filter_by(code=settings.payment.VIDEO_REVIEW_PROMO)
    promo_result = await session.execute(promo_query)
    promocode = promo_result.scalar_one_or_none()

    if not promocode:
        # Create promocode if it doesn't exist
        promocode = PromocodeModel(
            code=settings.payment.VIDEO_REVIEW_PROMO,
            discount_amount=settings.payment.VIDEO_REVIEW_DISCOUNT,
            is_active=True,
            max_uses=None,  # Unlimited uses
        )
        session.add(promocode)
        await session.flush()

    # Create video review record
    video_review = VideoReviewModel(
        user_id=user_id,
        video_file_id=message.video.file_id,
        promocode_id=promocode.id,
        is_approved=True,  # Auto-approve
    )
    session.add(video_review)
    await session.commit()

    logger.info(f"User {user_id} uploaded video review, granted promocode {promocode.code}")

    # Send success message
    text = (
        "✅ <b>Спасибо за видео-отзыв!</b>\n\n"
        f"🎁 Ваш промокод: <code>{settings.payment.VIDEO_REVIEW_PROMO}</code>\n"
        f"💰 Скидка: {settings.payment.VIDEO_REVIEW_DISCOUNT} ₽\n\n"
        "📝 Используйте этот промокод при оплате любого тарифа!\n\n"
        "<i>Промокод можно использовать один раз</i>"
    )

    await message.answer(text, reply_markup=back_to_main_keyboard())
    await state.clear()


@router.message(VideoReviewStates.waiting_for_video)
async def wrong_video_format(message: Message) -> None:
    """
    Handle wrong format when waiting for video.

    Args:
        message: Message
    """
    await message.answer(
        "⚠️ Пожалуйста, отправьте видео-файл.\n\n"
        "Нажмите 📎 (скрепка) → Видео и выберите файл с вашего устройства"
    )
