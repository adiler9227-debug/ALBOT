import aiosqlite
from datetime import datetime, timedelta
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
                subscription_end DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица платежей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                subscription_type TEXT,
                photo_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица расписаний
        await db.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_type TEXT,
                date DATE,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица отложенных постов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                photo_id TEXT,
                publish_time TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

async def get_user(user_id: int):
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_subscription(user_id: int, days: int):
    """Обновить подписку пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(user_id)
        
        if user and user['subscription_end']:
            # Если подписка еще активна, продлеваем
            current_end = datetime.fromisoformat(user['subscription_end'])
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
        else:
            # Новая подписка
            new_end = datetime.now() + timedelta(days=days)
        
        await db.execute(
            'UPDATE users SET subscription_end = ? WHERE user_id = ?',
            (new_end.isoformat(), user_id)
        )
        await db.commit()
        return new_end

async def get_days_left(user_id: int) -> int:
    """Получить количество оставшихся дней подписки"""
    user = await get_user(user_id)
    if not user or not user['subscription_end']:
        return 0
    
    end_date = datetime.fromisoformat(user['subscription_end'])
    days_left = (end_date - datetime.now()).days
    return max(0, days_left)

async def add_payment(user_id: int, amount: int, subscription_type: str, photo_id: str):
    """Добавить платеж на проверку"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'INSERT INTO payments (user_id, amount, subscription_type, photo_id) VALUES (?, ?, ?, ?)',
            (user_id, amount, subscription_type, photo_id)
        )
        await db.commit()
        return cursor.lastrowid

async def get_pending_payments():
    """Получить платежи на проверку"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM payments WHERE status = "pending" ORDER BY created_at DESC'
        ) as cursor:
            return await cursor.fetchall()

async def update_payment_status(payment_id: int, status: str):
    """Обновить статус платежа"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE payments SET status = ? WHERE id = ?',
            (status, payment_id)
        )
        await db.commit()

async def save_schedule(schedule_type: str, date: str, content: str):
    """Сохранить расписание"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO schedules (schedule_type, date, content) VALUES (?, ?, ?)',
            (schedule_type, date, content)
        )
        await db.commit()

async def get_schedule(date: str = None):
    """Получить расписание"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if date:
            async with db.execute('SELECT * FROM schedules WHERE date = ?', (date,)) as cursor:
                return await cursor.fetchone()
        else:
            async with db.execute('SELECT * FROM schedules ORDER BY date') as cursor:
                return await cursor.fetchall()

async def add_scheduled_post(content: str, publish_time: datetime, photo_id: str = None):
    """Добавить отложенный пост"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO scheduled_posts (content, photo_id, publish_time) VALUES (?, ?, ?)',
            (content, photo_id, publish_time.isoformat())
        )
        await db.commit()

async def get_pending_posts():
    """Получить посты готовые к публикации"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute(
            'SELECT * FROM scheduled_posts WHERE status = "scheduled" AND publish_time <= ?',
            (now,)
        ) as cursor:
            return await cursor.fetchall()

async def mark_post_published(post_id: int):
    """Отметить пост как опубликованный"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE scheduled_posts SET status = "published" WHERE id = ?',
            (post_id,)
        )
        await db.commit()
