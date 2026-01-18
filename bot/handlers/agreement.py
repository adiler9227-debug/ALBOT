"""Agreement handler."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import main_keyboard
from bot.services import set_agreement

router = Router(name="agreement")


@router.callback_query(F.data == "agreement:agree")
async def agreement_agree_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    """
    Handle agreement acceptance.

    Args:
        callback: Callback query
        session: Database session
    """
    if not callback.from_user:
        return

    # Set agreement in database
    await set_agreement(session, callback.from_user.id)

    # Show welcome message with main menu
    welcome_text = (
        f"✅ Спасибо за принятие!\n\n"
        f"👋 Добро пожаловать, {callback.from_user.first_name}!\n\n"
        "Добро пожаловать в мир дыхательных практик и Кундалини йоги 🧘‍♀️\n\n"
        "Этот бот — твой проводник и помощник, с которым ты сможешь:\n\n"
        "• Научиться справляться с тревожностью и стрессом\n"
        "• Избавиться от хронической усталости и апатии\n"
        "• Избавиться от отёчности и лишнего веса\n"
        "• Стать более энергичной и уверенной\n"
        "• Улучшить сон и общее самочувствие\n"
        "• Повысить либидо и сексуальность\n"
        "• Улучшить память и когнитивные функции\n"
        "• Избавиться от зависимостей\n"
        "• Укрепить внутреннюю опору\n\n"
        "Начнём с малого 👇"
    )

    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=main_keyboard(),
    )
    await callback.answer("Согласие принято")
