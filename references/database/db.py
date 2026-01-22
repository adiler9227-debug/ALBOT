import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import DB_PATH

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                agreed INTEGER DEFAULT 0,
                expiry_date DATE,
                first_lesson_started INTEGER DEFAULT 0,
                lesson_clicked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица платежей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tariff TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        await db.commit()

async def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавить нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
            (user_id, username, first_name)
        )
        await db.commit()

async def get_user(user_id: int) -> Optional[Dict]:
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_user_agreed(user_id: int, agreed: bool = True):
    """Обновить согласие с офертой"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET agreed = ? WHERE user_id = ?',
            (1 if agreed else 0, user_id)
        )
        await db.commit()

async def update_first_lesson_started(user_id: int):
    """Отметить начало первого урока"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET first_lesson_started = 1 WHERE user_id = ?',
            (user_id,)
        )
        await db.commit()

async def update_lesson_clicked(user_id: int, clicked: bool = True):
    """Обновить статус клика по уроку"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET lesson_clicked = ? WHERE user_id = ?',
            (1 if clicked else 0, user_id)
        )
        await db.commit()

async def update_expiry_date(user_id: int, days: int):
    """Обновить дату истечения подписки"""
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(user_id)

        if user and user['expiry_date']:
            # Если подписка еще активна, продлеваем
            current_end = datetime.fromisoformat(user['expiry_date'])
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
        else:
            # Новая подписка
            new_end = datetime.now() + timedelta(days=days)

        await db.execute(
            'UPDATE users SET expiry_date = ? WHERE user_id = ?',
            (new_end.isoformat(), user_id)
        )
        await db.commit()
        return new_end

async def get_days_left(user_id: int) -> int:
    """Получить количество оставшихся дней подписки"""
    user = await get_user(user_id)
    if not user or not user['expiry_date']:
        return 0

    end_date = datetime.fromisoformat(user['expiry_date'])
    days_left = (end_date - datetime.now()).days
    return max(0, days_left)

async def add_payment(user_id: int, amount: int, tariff: str):
    """Добавить платеж"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO payments (user_id, amount, tariff) VALUES (?, ?, ?)',
            (user_id, amount, tariff)
        )
        await db.commit()

async def get_user_payments(user_id: int) -> List[Dict]:
    """Получить историю платежей пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM payments WHERE user_id = ? ORDER BY date DESC',
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_expired_users() -> List[int]:
    """Получить пользователей с истекшей подпиской"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute(
            'SELECT user_id FROM users WHERE expiry_date IS NOT NULL AND expiry_date < ?',
            (now,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]
