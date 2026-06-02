from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from config import config
from database import DB
from keyboards import cancel_kb, main_menu

router = Router()


class OrderForm(StatesGroup):
    full_name = State()
    phone = State()
    province = State()
    city = State()
    address = State()
    postal_code = State()


async def get_product(product_id: int):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


@router.callback_query(F.data.startswith("buy:"))
async def start_purchase(cb: CallbackQuery, state: FSMContext):
    product_id = int(cb.data.split(":")[1])
    p = await get_product(product_id)
    if not p or p["stock"] <= 0:
        await cb.answer("این محصول موجود نیست.", show_alert=True)
        return
    await state.update_data(product_id=product_id)
    await state.set_state(OrderForm.full_name)
    await cb.message.answer("📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=cancel_kb())
    await cb.answer()


@router.message(OrderForm.full_name)
async def get_full_name(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return
    await state.update_data(full_name=msg.text)
    await state.set_state(OrderForm.phone)
    await msg.answer("📱 شماره موبایل:")


@router.message(OrderForm.phone)
async def get_phone(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return
    await state.update_data(phone=msg.text)
    await state.set_state(OrderForm.province)
    await msg.answer("🗺 استان:")


@router.message(OrderForm.province)
async def get_province(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return
    await state.update_data(province=msg.text)
    await state.set_state(OrderForm.city)
    await msg.answer("🏙 شهر:")


@router.message(OrderForm.city)
async def get_city(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return
    await state.update_data(city=msg.text)
    await state.set_state(OrderForm.address)
    await msg.answer("🏠 آدرس کامل:")


@router.message(OrderForm.address)
async def get_address(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return
    await state.update_data(address=msg.text)
    await state.set_state(OrderForm.postal_code)
    await msg.answer("📮 کد پستی:")


@router.message(OrderForm.postal_code)
async def get_postal_code(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("انصراف داده شد.", reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))
        return

    data = await state.get_data()
    await state.clear()

    p = await get_product(data["product_id"])
    if not p or p["stock"] <= 0:
        await msg.answer("متأسفانه این محصول به اتمام رسید.")
        return

    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id FROM users WHERE tg_id=?", (msg.from_user.id,)) as cur:
            user = await cur.fetchone()
        if not user:
            await msg.answer("خطا: کاربر یافت نشد. /start را بزنید.")
            return

        await db.execute("""
            INSERT INTO orders (user_id, product_id, quantity, total_price, status,
                full_name, phone, province, city, address, postal_code)
            VALUES (?, ?, 1, ?, 'pending', ?, ?, ?, ?, ?, ?)
        """, (user["id"], p["id"], p["price"],
              data["full_name"], data["phone"], data["province"],
              data["city"], data["address"], msg.text))
        await db.execute("UPDATE products SET stock=stock-1 WHERE id=?", (p["id"],))
        order_id = (await (await db.execute("SELECT last_insert_rowid()")).fetchone())[0]
        await db.commit()

    invoice = (
        f"🧾 <b>فاکتور سفارش #{order_id}</b>\n\n"
        f"📦 محصول: {p['title']}\n"
        f"💰 مبلغ: {p['price']:,} تومان\n\n"
        f"👤 نام: {data['full_name']}\n"
        f"📱 موبایل: {data['phone']}\n"
        f"🗺 استان: {data['province']}\n"
        f"🏙 شهر: {data['city']}\n"
        f"🏠 آدرس: {data['address']}\n"
        f"📮 کد پستی: {msg.text}\n\n"
        f"⏳ وضعیت: در انتظار تأیید"
    )
    await msg.answer(invoice, reply_markup=main_menu(msg.from_user.id == config.ADMIN_ID))

    from keyboards import order_status_kb
    admin_text = (
        f"🔔 <b>سفارش جدید #{order_id}</b>\n\n"
        f"📦 {p['title']} — {p['price']:,} تومان\n"
        f"👤 {data['full_name']} | {data['phone']}\n"
        f"📍 {data['province']}، {data['city']}\n"
        f"🏠 {data['address']}\n"
        f"📮 {msg.text}"
    )
    from aiogram import Bot
    bot = Bot.get_current()
    if bot:
        await bot.send_message(config.ADMIN_ID, admin_text, reply_markup=order_status_kb(order_id))


@router.callback_query(F.data == "my:orders")
async def my_orders(cb: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.id, p.title, o.total_price, o.status, o.created_at
            FROM orders o JOIN users u ON o.user_id=u.id
            JOIN products p ON o.product_id=p.id
            WHERE u.tg_id=? ORDER BY o.id DESC LIMIT 10
        """, (cb.from_user.id,)) as cur:
            orders = await cur.fetchall()

    if not orders:
        await cb.message.edit_text("📭 هنوز سفارشی ثبت نکرده‌اید.")
        return await cb.answer()

    status_map = {"pending": "⏳ در انتظار", "confirmed": "✅ تأیید شده",
                  "shipped": "🚚 ارسال شده", "completed": "🎉 تکمیل", "rejected": "❌ رد شده"}
    text = "📦 <b>سفارشات شما:</b>\n\n"
    for o in orders:
        text += f"#{o['id']} — {o['title']} — {o['total_price']:,} تومان — {status_map.get(o['status'], o['status'])}\n"
    await cb.message.edit_text(text)
    await cb.answer()
