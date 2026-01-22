# 🚀 Railway Deployment Guide

## ✅ Pre-deployment Checklist

### 1. Database & Cache Services Created
- ✅ PostgreSQL database added in Railway
- ✅ Redis cache added in Railway
- ✅ `DATABASE_URL` automatically set by Railway
- ✅ `REDIS_URL` automatically set by Railway

### 2. Environment Variables Required

Add these in Railway dashboard → Variables:

```env
BOT_TOKEN=8387775247:AAEpMDc-JAmdD5jzTCrQ6BP5kb1h9qSXmCg
CHANNEL_ID=-3394467411
```

**Note:** `DATABASE_URL` and `REDIS_URL` are auto-created by Railway when you add PostgreSQL/Redis services.

---

## 🔧 Deployment Process

### Railway will automatically:

1. **Build the Docker container** from `Dockerfile`
2. **Run migrations**: `alembic upgrade head` (creates all tables)
3. **Start the bot**: `python -m bot`
4. **Health check**: `/health` endpoint on port from `$PORT`

---

## 📊 Database Tables Created

After `alembic upgrade head` runs, these tables will be created:

- ✅ `users` - User accounts
- ✅ `subscriptions` - Active subscriptions
- ✅ `payments` - Payment transactions
- ✅ `agreements` - User consent tracking
- ✅ `lesson_progress` - Free lesson viewing
- ✅ `promocodes` - Promocode system
- ✅ `promocode_usage` - Usage tracking
- ✅ `referrals` - Referral program
- ✅ `video_reviews` - Video testimonials

---

## 💳 Payment Integration

### Prodamus Links Connected

| Tariff | Price | Days | Prodamus Link |
|--------|-------|------|---------------|
| 🌱 Пробная неделя | 490 ₽ | 7 | https://payform.ru/4lanBvw/ |
| 📅 1 месяц | 1990 ₽ | 30 | https://payform.ru/4kanBwA/ |
| 📆 3 месяца | 4990 ₽ | 90 | https://payform.ru/5canBwZ/ |
| 🌟 6 месяцев | 8990 ₽ | 180 | https://payform.ru/66anBxq/ |
| ⭐ 1 год | 16490 ₽ | 365 | https://payform.ru/6tanBxN/ |

### Webhook Configuration

After deployment, configure Prodamus webhook:

1. Get your Railway URL: `https://your-app.up.railway.app`
2. Set webhook URL in Prodamus: `https://your-app.up.railway.app/prodamus-webhook`
3. Secret key is already configured in code

### How Payments Work

1. User selects tariff (7/30/90/180/365 days)
2. Bot generates: `{prodamus_link}?order_id=user_{user_id}_days_{days}`
3. User pays on Prodamus
4. Prodamus sends webhook
5. Bot activates subscription for correct days
6. User gets channel invite

---

## 🎁 Features Enabled

- ✅ Referral program (+30 days bonus)
- ✅ Video reviews (VIDEOOTZIV promocode, -1000₽)
- ✅ Auto reminders (48-72h, 3 days before expiry)
- ✅ Daily auto-kick at 00:00

---

## 🧪 Testing After Deploy

1. `/start` command
2. Payment flow for each tariff
3. Webhook receives notifications
4. User added to channel
5. Referral link generation

---

## ✨ Ready for Production!
