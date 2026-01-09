# 🤖 Telegram Bot - Breathing & Kundalini Yoga Club

Professional Telegram bot built with aiogram 3, SQLAlchemy 2.0, PostgreSQL, and Redis for subscription management and payment processing.

## ✨ Features

### Core Functionality

1. **Agreement System**
   - Mandatory agreement with terms before using the bot
   - Three documents: Offer, Privacy Policy, Consent
   - Blocked access until user agrees

2. **Lesson System**
   - Breathing lessons with video content
   - 10-minute reminder timer using `asyncio`
   - Automatic notification with sad cat photo if lesson not started
   - Progress tracking per user

3. **Telegram Payments Integration**
   - Native Telegram Payments API
   - Three tariffs: 30/90/365 days
   - Automatic subscription management
   - Payment history tracking

4. **Auto-kick Scheduler**
   - Daily cron job at 00:00
   - Automatic removal of expired users from channel
   - Ban + unban mechanism
   - Notification to affected users

5. **Personal Account**
   - Days remaining display
   - Payment history
   - Subscription management

## 🏗️ Architecture

Built on professional aiogram 3 template:

```
bot/
├── __main__.py              # Entry point
├── core/
│   └── config.py           # Pydantic settings
├── database/
│   ├── database.py         # SQLAlchemy async engine
│   └── models/             # Database models
│       ├── base.py         # Base model
│       ├── user.py         # User model
│       ├── subscription.py # Subscription model
│       ├── payment.py      # Payment model
│       ├── agreement.py    # Agreement model
│       └── lesson_progress.py # Lesson progress
├── handlers/               # Message/callback handlers
│   ├── start.py
│   ├── agreement.py
│   ├── lessons.py
│   ├── payments.py
│   ├── subscription.py
│   └── menu.py
├── keyboards/
│   └── inline/            # Inline keyboards
│       ├── agreement.py
│       ├── tariffs.py
│       ├── subscription.py
│       └── menu.py
├── middlewares/           # Aiogram middlewares
│   ├── database.py       # Session injection
│   └── auth.py           # User registration
├── services/             # Business logic
│   ├── users.py
│   ├── subscriptions.py
│   ├── payments.py
│   └── channel.py
├── scheduler.py          # APScheduler tasks
└── locales/              # i18n translations

migrations/               # Alembic migrations
docker-compose.yml       # Docker services
```

## 📦 Installation

### Using Docker (Recommended)

1. Clone repository:
```bash
git clone <repo>
cd ALBOT
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Configure `.env`:
```env
BOT_TOKEN=your_bot_token
PAYMENT_TOKEN=your_payment_token
CHANNEL_ID=-1001234567890

DB_HOST=postgres
DB_USER=postgres
DB_PASS=postgres
DB_NAME=bot_db

REDIS_HOST=redis
```

4. Start services:
```bash
docker-compose up -d
```

5. Check logs:
```bash
docker-compose logs -f bot
```

### Local Development

1. Install Python 3.12+

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup PostgreSQL and Redis

4. Create `.env` file

5. Run migrations:
```bash
alembic upgrade head
```

6. Start bot:
```bash
python -m bot
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | `123456:ABC-DEF...` |
| `PAYMENT_TOKEN` | Payment provider token | `123456:TEST:...` |
| `CHANNEL_ID` | Private channel ID | `-1001234567890` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASS` | Database password | `postgres` |
| `DB_NAME` | Database name | `bot_db` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |

### Obtaining Tokens

**BOT_TOKEN:**
1. Open [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions
4. Copy token

**PAYMENT_TOKEN:**
1. Open [@BotFather](https://t.me/BotFather)
2. Send `/mybots` → Select bot → Payments
3. Choose provider (YooKassa, Stripe, etc.)
4. Copy payment token

**CHANNEL_ID:**
1. Add bot as administrator to channel
2. Forward message from channel to [@userinfobot](https://t.me/userinfobot)
3. Copy channel ID

### Tariff Configuration

Edit in `bot/core/config.py`:

```python
class PaymentSettings(EnvBaseSettings):
    TARIFF_30_DAYS: int = 30
    TARIFF_30_PRICE: int = 199000  # 1990 RUB in kopecks
    TARIFF_90_DAYS: int = 90
    TARIFF_90_PRICE: int = 477000  # 4770 RUB in kopecks
    TARIFF_365_DAYS: int = 365
    TARIFF_365_PRICE: int = 1590000  # 15900 RUB in kopecks
```

## 🗄️ Database Schema

### Tables

**users**
- `id` - User ID (primary key)
- `first_name`, `last_name`, `username` - User info
- `language_code` - User language
- `is_admin`, `is_premium` - Flags
- `created_at` - Registration date

**subscriptions**
- `id` - Subscription ID (primary key)
- `user_id` - Foreign key to users
- `expiry_date` - Subscription end date
- `tariff_days` - Tariff duration
- `is_active` - Active flag
- `created_at` - Creation date

**payments**
- `id` - Payment ID (primary key)
- `user_id` - Foreign key to users
- `amount` - Amount in kopecks
- `currency` - Currency code (RUB)
- `tariff_days` - Purchased tariff
- `payment_date` - Payment timestamp
- `provider_payment_charge_id` - Provider charge ID

**agreements**
- `id` - Agreement ID (primary key)
- `user_id` - Foreign key to users
- `agreed` - Agreement status
- `agreed_at` - Agreement timestamp

**lesson_progress**
- `id` - Progress ID (primary key)
- `user_id` - Foreign key to users
- `first_lesson_started_at` - Start timestamp
- `lesson_clicked` - Clicked flag
- `reminder_sent` - Reminder sent flag

## 🚀 Deployment

### Docker Compose

Services included:
- `postgres` - PostgreSQL 16
- `redis` - Redis 7
- `migrator` - Alembic migrations
- `bot` - Telegram bot

### Railway / Render

1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically

## 📊 Tech Stack

- **aiogram 3.15** - Async Telegram Bot framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL 16** - Database
- **Redis 7** - Cache & FSM storage
- **Alembic** - Database migrations
- **APScheduler** - Task scheduling
- **Pydantic 2** - Settings validation
- **Loguru** - Logging
- **uvloop** - High-performance event loop

## 🔐 Security

- Environment variables for secrets
- `.env` in `.gitignore`
- PostgreSQL connection pooling
- Rate limiting support
- Proper error handling

## 📝 Usage

### User Flow

1. `/start` - Start bot
2. Accept agreement with documents
3. Main menu:
   - 🫁 Watch breathing lesson
   - 🌿 Join breathing club
   - 👤 My account
4. Purchase subscription
5. Access private channel

### Admin

Bot automatically tracks:
- New user registrations
- Payment processing
- Subscription expiry
- Daily auto-kick job

## 🛠️ Development

### Creating Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
ruff check .
ruff format .
```

## 🐛 Troubleshooting

**Bot doesn't start:**
- Check `BOT_TOKEN` in `.env`
- Verify PostgreSQL is running
- Check logs: `docker-compose logs bot`

**Payments don't work:**
- Verify `PAYMENT_TOKEN` is correct
- Check payment provider is configured in @BotFather
- Test with test payment token first

**Users not kicked:**
- Verify bot is admin in channel
- Check `CHANNEL_ID` is correct
- Check scheduler logs

## 📄 License

MIT License

## 🤝 Contributing

Pull requests are welcome!

## 💬 Support

For issues and questions, create GitHub issue.
