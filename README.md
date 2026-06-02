# 🛍 DorbinHome — Telegram Channel Shop Bot

بات فروشگاهی تلگرام با قابلیت انتشار محصول در کانال، مدیریت سفارشات و گزارش فروش.

## ✨ امکانات
- افزودن محصول با تصویر، توضیحات، مشخصات، قیمت و موجودی
- انتشار خودکار محصول در کانال تلگرام با دکمه خرید
- فرم ثبت سفارش (نام، موبایل، استان، شهر، آدرس، کد پستی)
- مدیریت سفارشات (تأیید / رد / ارسال شد)
- اطلاع‌رسانی به کاربر در هر تغییر وضعیت
- گزارش فروش و آمار کاربران
- پایگاه داده SQLite (بدون نیاز به PostgreSQL/Redis)

## 🚀 نصب سریع روی VPS

```bash
git clone https://github.com/moha100h/dorbinhome.git
cd dorbinhome
chmod +x install.sh
./install.sh
```

## 📋 دستورات مفید

```bash
docker compose logs -f bot    # مشاهده لاگ
docker compose restart bot    # ری‌استارت
docker compose down           # توقف
docker compose up -d          # شروع مجدد
```

## 🛠 توسعه محلی

```bash
cd bot
pip install -r requirements.txt
cp ../.env.example ../.env    # ویرایش .env
python main.py
```
