import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN', '8387775247:AAEpMDc-JAmdD5jzTCrQ6BP5kb1h9qSXmCg')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7737327242'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003574169604'))

# Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyC8pSz7DA30xueWrgLs1qJxAjP5TWD2hrU')

# База данных
DB_PATH = 'database/subscriptions.db'

# Цены на подписку (в рублях)
SUBSCRIPTION_PRICES = {
    '1_month': 1990,
    '3_months': 4770,
    '6_months': 8940,
    '12_months': 15900
}

SUBSCRIPTION_DAYS = {
    '1_month': 30,
    '3_months': 90,
    '6_months': 180,
    '12_months': 365
}
