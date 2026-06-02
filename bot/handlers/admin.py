from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite
from config import config
from database import DB
from keyboards import admin_panel_kb, channel_product_kb, cancel_kb, order_status_kb

router = Router()


def admin_only(func):
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id if hasattr(event, "from_user") else 0
        if uid != config.ADMIN_ID:
            if hasattr(event, "answer"):
                await event.answer("دسترسی ندارید.", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    wrapper.__wrapped__ = func
    return wrapper


class AddProduct(StatesGroup):
    title = State()
    description = State()
    specs = State()
    price = State()
    stock = State()
    images = State()


@router.callback_query(F.data == "admin:panel")
async def admin_panel(cb: CallbackQuery):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    await cb.message.edit_text("👑 پنل مدیریت:", reply_markup=admin_panel_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:add_product")
async def add_product_start(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    await state.set_state(AddProduct.title)
    await cb.message.answer("📝 عنوان محصول:", reply_markup=cancel_kb())
    await cb.answer()


@router.message(AddProduct.title)
async def ap_title(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("لغو شد.")
        return
    await state.update_data(title=msg.text)
    await state.set_state(AddProduct.description)
    await msg.answer("📄 توضیحات محصول:")


@router.message(AddProduct.description)
async def ap_desc(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("لغو شد.")
        return
    await state.update_data(description=msg.text)
    await state.set_state(AddProduct.specs)
    await msg.answer("📋 مشخصات فنی (یا - برای رد کردن):")


@router.message(AddProduct.specs)
async def ap_specs(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("لغو شد.")
        return
    await state.update_data(specs=None if msg.text == "-" else msg.text)
    await state.set_state(AddProduct.price)
    await msg.answer("💰 قیمت (تومان):")


@router.message(AddProduct.price)
async def ap_price(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("لغو شد.")
        return
    try:
        price = int(msg.text.replace(",", "").replace("،", ""))
    except ValueError:
        await msg.answer("عدد صحیح وارد کنید:")
        return
    await state.update_data(price=price)
    await state.set_state(AddProduct.stock)
    await msg.answer("📊 تعداد موجودی:")


@router.message(AddProduct.stock)
async def ap_stock(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("لغو شد.")
        return
    try:
        stock = int(msg.text)
    except ValueError:
        await msg.answer("عدد صحیح وارد کنید:")
        return
    await state.update_data(stock=stock, images=[])
    await state.set_state(AddProduct.images)
    await msg.answer("🖼 تصاویر محصول را ارسال کنید (یک یا چند عکس)\nبرای پایان: /done")


@router.message(AddProduct.images, F.photo)
async def ap_image(msg: Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    images.append(msg.photo[-1].file_id)
    await state.update_data(images=images)
    await msg.answer(f"✅ عکس {len(images)} دریافت شد. ادامه دهید یا /done بزنید.")


@router.message(AddProduct.images, F.text == "/done")
async def ap_done(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO products (title, description, specs, price, stock) VALUES (?,?,?,?,?)",
            (data["title"], data["description"], data.get("specs"), data["price"], data["stock"])
        )
        product_id = (await (await db.execute("SELECT last_insert_rowid()")).fetchone())[0]
        for fid in data.get("images", []):
            await db.execute("INSERT INTO product_images (product_id, file_id) VALUES (?,?)", (product_id, fid))
        await db.commit()

    await msg.answer(f"✅ محصول #{product_id} اضافه شد.")

    if config.CHANNEL_ID:
        me = await bot.get_me()
        caption = (
            f"📦 <b>{data['title']}</b>\n\n"
            f"{data['description'] or ''}\n\n"
            f"💰 قیمت: <b>{data['price']:,} تومان</b>\n"
            f"📊 موجودی: {data['stock']} عدد"
        )
        kb = channel_product_kb(me.username, product_id)
        images = data.get("images", [])
        try:
            if images:
                sent = await bot.send_photo(config.CHANNEL_ID, images[0], caption=caption, reply_markup=kb)
            else:
                sent = await bot.send_message(config.CHANNEL_ID, caption, reply_markup=kb)
            async with aiosqlite.connect(DB) as db:
                await db.execute("UPDATE products SET channel_msg_id=? WHERE id=?", (sent.message_id, product_id))
                await db.commit()
            await msg.answer("📢 محصول در کانال منتشر شد.")
        except Exception as e:
            await msg.answer(f"⚠️ خطا در انتشار کانال: {e}")


@router.callback_query(F.data == "admin:products")
async def admin_products(cb: CallbackQuery):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products ORDER BY id DESC") as cur:
            products = await cur.fetchall()
    if not products:
        await cb.message.edit_text("📭 محصولی وجود ندارد.")
        return await cb.answer()
    text = "📦 <b>لیست محصولات:</b>\n\n"
    for p in products:
        text += f"#{p['id']} — {p['title']} — {p['price']:,} تومان — موجودی: {p['stock']}\n"
    await cb.message.edit_text(text, reply_markup=admin_panel_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:orders")
async def admin_orders(cb: CallbackQuery):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.id, p.title, o.total_price, o.status, o.full_name, o.phone
            FROM orders o JOIN products p ON o.product_id=p.id
            ORDER BY o.id DESC LIMIT 20
        """) as cur:
            orders = await cur.fetchall()
    if not orders:
        await cb.message.edit_text("📭 سفارشی وجود ندارد.")
        return await cb.answer()
    status_map = {"pending": "⏳", "confirmed": "✅", "shipped": "🚚", "completed": "🎉", "rejected": "❌"}
    text = "📋 <b>سفارشات اخیر:</b>\n\n"
    for o in orders:
        text += f"{status_map.get(o['status'], '?')} #{o['id']} — {o['title']} — {o['total_price']:,} تومان — {o['full_name']}\n"
    await cb.message.edit_text(text, reply_markup=admin_panel_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:report")
async def admin_report(cb: CallbackQuery):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*), SUM(total_price) FROM orders WHERE status != 'rejected'") as cur:
            total = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'") as cur:
            pending = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users = (await cur.fetchone())[0]
    text = (
        f"📊 <b>گزارش فروش:</b>\n\n"
        f"👥 کاربران: {users}\n"
        f"📦 کل سفارشات: {total[0]}\n"
        f"⏳ در انتظار: {pending}\n"
        f"💰 درآمد کل: {(total[1] or 0):,} تومان"
    )
    await cb.message.edit_text(text, reply_markup=admin_panel_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:channel")
async def admin_channel(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    await cb.message.answer(f"کانال فعلی: <code>{config.CHANNEL_ID or 'تنظیم نشده'}</code>\nبرای تغییر، آیدی کانال را بفرستید (مثلاً @mychannel):")
    await cb.answer()


@router.callback_query(F.data.startswith("order:"))
async def handle_order_action(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id != config.ADMIN_ID:
        return await cb.answer("دسترسی ندارید.", show_alert=True)
    _, action, order_id = cb.data.split(":")
    order_id = int(order_id)
    status_map = {"confirm": "confirmed", "reject": "rejected", "ship": "shipped"}
    new_status = status_map.get(action)
    if not new_status:
        return await cb.answer()

    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT o.*, u.tg_id FROM orders o JOIN users u ON o.user_id=u.id WHERE o.id=?", (order_id,)) as cur:
            order = await cur.fetchone()
        if not order:
            return await cb.answer("سفارش یافت نشد.")
        await db.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        await db.commit()

    label = {"confirmed": "✅ تأیید شد", "rejected": "❌ رد شد", "shipped": "🚚 ارسال شد"}
    await cb.message.edit_text(cb.message.text + f"\n\n{label[new_status]}")
    await cb.answer(label[new_status])

    msg_to_user = {
        "confirmed": f"✅ سفارش #{order_id} شما تأیید شد.",
        "rejected": f"❌ سفارش #{order_id} شما رد شد.",
        "shipped": f"🚚 سفارش #{order_id} شما ارسال شد.",
    }
    try:
        await bot.send_message(order["tg_id"], msg_to_user[new_status])
    except Exception:
        pass
