import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')  # Провайдер платежей Telegram
CHANNEL_ID = os.getenv('CHANNEL_ID')  # ID канала для автоматического кика

# База данных
DB_PATH = os.getenv('DB_PATH', 'database/bot.db')

# Тарифы (в рублях)
TARIFFS = {
    '30': {
        'days': 30,
        'price': 1990,
        'title': '1 месяц подписки',
        'description': 'Доступ к курсу на 30 дней'
    },
    '90': {
        'days': 90,
        'price': 4770,
        'title': '3 месяца подписки',
        'description': 'Доступ к курсу на 90 дней'
    },
    '365': {
        'days': 365,
        'price': 15900,
        'title': '12 месяцев подписки',
        'description': 'Доступ к курсу на 365 дней'
    }
}

# URL документов
OFERTA_URL = os.getenv('OFERTA_URL', 'https://example.com/oferta.pdf')
PRIVACY_URL = os.getenv('PRIVACY_URL', 'https://example.com/privacy.pdf')

# Таймер напоминания (в секундах)
REMINDER_DELAY = 600  # 10 минут

# Фото грустного кота (file_id или URL)
SAD_CAT_PHOTO = os.getenv('SAD_CAT_PHOTO', 'https://i.imgur.com/sad_cat.jpg')
