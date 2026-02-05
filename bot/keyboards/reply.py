from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Урок по дыханию"), KeyboardButton(text="Клуб дыхания")],
        [KeyboardButton(text="Дней осталось"), KeyboardButton(text="Продлить подписку")],
        [KeyboardButton(text="Служба заботы")]
    ],
    resize_keyboard=True,
    persistent=True
)
