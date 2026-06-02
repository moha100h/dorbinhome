# 🛍 DorbinHome — Telegram Channel Shop Bot

بات فروشگاهی تلگرام — Python 3.11 + aiogram 3 + SQLite + Docker

---

## ✨ امکانات

- 🛍 لیست محصولات با کارت و عکس
- 🛒 فرم خرید کامل با اعتبارسنجی (نام، موبایل، استان، شهر، آدرس، کدپستی)
- 📦 تاریخچه سفارشات کاربر
- 👑 پنل ادمین: افزودن/ویرایش/حذف محصول، مدیریت سفارشات، گزارش فروش
- 📢 انتشار خودکار محصول در کانال با دکمه خرید
- 🔔 نوتیف به کاربر در هر تغییر وضعیت سفارش

---

## 🚀 نصب روی VPS

### پیش‌نیاز
- Ubuntu 20.04+ یا Debian 11+
- دسترسی root

### مراحل نصب

```bash
# ۱. کلون ریپو
git clone https://github.com/moha100h/dorbinhome.git
cd dorbinhome

# ۲. اجرای نصب‌کننده
chmod +x install.sh
./install.sh
```

اسکریپت می‌پرسد:
- **Bot Token** — از @BotFather
- **Admin ID** — آیدی عددی شما (از @userinfobot)
- **Channel ID** — مثلاً `@mychannel` (اختیاری)

---

## 📋 دستورات مدیریت

```bash
# لاگ زنده
docker compose logs -f bot

# ری‌استارت
docker compose restart bot

# توقف
docker compose down

# آپدیت
git pull && docker compose up -d --build

# ری‌ست کامل (حذف دیتابیس)
docker compose down -v
```

---

## ⚙️ تنظیمات (.env)

```env
BOT_TOKEN=توکن_بات
ADMIN_ID=آیدی_عددی_ادمین
CHANNEL_ID=@آیدی_کانال
DB_PATH=/data/shop.db
```

بعد از تغییر `.env`:
```bash
docker compose restart bot
```
