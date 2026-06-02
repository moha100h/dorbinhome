from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter
from bot.db.repo import (
    create_product, get_all_products, get_product, update_product,
    delete_product, add_image, get_images, get_all_orders,
    set_order_status, get_order, sales_stats, best_sellers, count_users
)
from bot.keyboards import admin_menu, main_menu, admin_products_kb, admin_product_kb, order_action_kb, channel_product_kb
from bot.utils.fmt import admin_order_card, STATUS_FA
from bot.core.config import ADMIN_ID, CHANNEL_ID

router = Router()


class AdminFilter(Filter):
    async def __call__(self, event) -> bool:
        uid = getattr(getattr(event, "from_user", None), "id", None)
        return uid == ADMIN_ID


router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class AddProductFSM(StatesGroup):
    title = State()
    description = State()
    specs = State()
    price = State()
    stock = State()
    images = State()


class EditFSM(StatesGroup):
    value = State()


@router.message(F.text == "👑 پنل مدیریت")
async def admin_panel(msg: Message):
    await msg.answer("👑 <b>پنل مدیریت:</b>", reply_markup=admin_menu())


@router.message(F.text == "🔙 منوی اصلی")
async def back_main(msg: Message):
    await msg.answer("منوی اصلی:", reply_markup=main_menu(True))


@router.callback_query(F.data == "admin:back")
async def admin_back_cb(cb: CallbackQuery):
    products = await get_all_products()
    await cb.message.edit_text("📦 <b>لیست محصولات:</b>", reply_markup=admin_products_kb(products))
    await cb.answer()


@router.callback_query(F.data == "admin:products")
async def admin_products_cb(cb: CallbackQuery):
    products = await get_all_products()
    if not products:
        await cb.message.edit_text("📭 محصولی وجود ندارد.")
        return await cb.answer()
    await cb.message.edit_text("📦 <b>لیست محصولات:</b>", reply_markup=admin_products_kb(products))
    await cb.answer()


# ─── add product ──────────────────────────────────────────────────────────────
@router.message(F.text == "➕ محصول جدید")
async def add_product_start(msg: Message, state: FSMContext):
    await state.set_state(AddProductFSM.title)
    from bot.keyboards import cancel_menu
    await msg.answer("📝 <b>عنوان محصول:</b>", reply_markup=cancel_menu())


@router.message(AddProductFSM.title)
async def ap_title(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear(); return await msg.answer("لغو شد.", reply_markup=admin_menu())
    if len(msg.text.strip()) < 2:
        return await msg.answer("⚠️ عنوان خیلی کوتاه است:")
    await state.update_data(title=msg.text.strip())
    await state.set_state(AddProductFSM.description)
    await msg.answer("📄 <b>توضیحات محصول:</b>")


@router.message(AddProductFSM.description)
async def ap_desc(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear(); return await msg.answer("لغو شد.", reply_markup=admin_menu())
    await state.update_data(description=msg.text.strip())
    await state.set_state(AddProductFSM.specs)
    await msg.answer("📋 <b>مشخصات فنی</b> (یا <code>-</code> برای رد کردن):")


@router.message(AddProductFSM.specs)
async def ap_specs(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear(); return await msg.answer("لغو شد.", reply_markup=admin_menu())
    await state.update_data(specs=None if msg.text.strip() == "-" else msg.text.strip())
    await state.set_state(AddProductFSM.price)
    await msg.answer("💰 <b>قیمت</b> (تومان):")


@router.message(AddProductFSM.price)
async def ap_price(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear(); return await msg.answer("لغو شد.", reply_markup=admin_menu())
    try:
        price = int(msg.text.strip().replace(",", "").replace("،", ""))
        assert price > 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد صحیح مثبت وارد کنید:")
    await state.update_data(price=price)
    await state.set_state(AddProductFSM.stock)
    await msg.answer("📦 <b>تعداد موجودی:</b>")


@router.message(AddProductFSM.stock)
async def ap_stock(msg: Message, state: FSMContext):
    if msg.text == "❌ انصراف":
        await state.clear(); return await msg.answer("لغو شد.", reply_markup=admin_menu())
    try:
        stock = int(msg.text.strip())
        assert stock >= 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد صحیح غیرمنفی وارد کنید:")
    await state.update_data(stock=stock, images=[])
    await state.set_state(AddProductFSM.images)
    await msg.answer("🖼 <b>تصاویر محصول</b> را ارسال کنید\nبعد از همه عکس‌ها: <code>/done</code>")


@router.message(AddProductFSM.images, F.photo)
async def ap_image(msg: Message, state: FSMContext):
    data = await state.get_data()
    imgs = data.get("images", [])
    imgs.append(msg.photo[-1].file_id)
    await state.update_data(images=imgs)
    await msg.answer(f"✅ عکس {len(imgs)} دریافت شد. ادامه دهید یا /done بزنید.")


@router.message(AddProductFSM.images, F.text == "/done")
async def ap_done(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    pid = await create_product(
        title=data["title"], description=data["description"],
        specs=data.get("specs"), price=data["price"], stock=data["stock"]
    )
    for i, fid in enumerate(data.get("images", [])):
        await add_image(pid, fid, i)
    await msg.answer(f"✅ محصول <b>#{pid}</b> اضافه شد!", reply_markup=admin_menu())
    if CHANNEL_ID:
        await _publish(bot, pid)
        await msg.answer("📢 در کانال منتشر شد.")


async def _publish(bot: Bot, pid: int):
    p = await get_product(pid)
    imgs = await get_images(pid)
    me = await bot.get_me()
    caption = (
        f"📦 <b>{p['title']}</b>\n\n{p['description'] or ''}\n\n"
        f"{'📋 ' + p['specs'] + chr(10) if p.get('specs') else ''}"
        f"💰 قیمت: <b>{p['price']:,} تومان</b>\n📦 موجودی: {p['stock']} عدد"
    )
    kb = channel_product_kb(me.username, pid)
    try:
        if imgs:
            sent = await bot.send_photo(CHANNEL_ID, imgs[0]["file_id"], caption=caption, reply_markup=kb)
        else:
            sent = await bot.send_message(CHANNEL_ID, caption, reply_markup=kb)
        await update_product(pid, channel_msg_id=sent.message_id)
    except Exception:
        pass


# ─── products ─────────────────────────────────────────────────────────────────
@router.message(F.text == "📦 محصولات")
async def list_products(msg: Message):
    products = await get_all_products()
    if not products:
        return await msg.answer("📭 محصولی وجود ندارد.")
    await msg.answer("📦 <b>لیست محصولات:</b>", reply_markup=admin_products_kb(products))


@router.callback_query(F.data.startswith("ap:view:"))
async def ap_view(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    p = await get_product(pid)
    if not p:
        return await cb.answer("یافت نشد.", show_alert=True)
    text = (
        f"📦 <b>{p['title']}</b>\n"
        f"💰 {p['price']:,} تومان\n"
        f"📦 موجودی: {p['stock']}\n"
        f"{'🟢 فعال' if p['active'] else '🔴 غیرفعال'}"
    )
    await cb.message.edit_text(text, reply_markup=admin_product_kb(pid, bool(p["active"])))
    await cb.answer()


@router.callback_query(F.data.startswith("ap:toggle:"))
async def ap_toggle(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    p = await get_product(pid)
    new = 0 if p["active"] else 1
    await update_product(pid, active=new)
    await cb.answer(f"{'🟢 فعال' if new else '🔴 غیرفعال'} شد.", show_alert=True)
    text = (
        f"📦 <b>{p['title']}</b>\n"
        f"💰 {p['price']:,} تومان\n"
        f"📦 موجودی: {p['stock']}\n"
        f"{'🟢 فعال' if new else '🔴 غیرفعال'}"
    )
    await cb.message.edit_text(text, reply_markup=admin_product_kb(pid, bool(new)))


@router.callback_query(F.data.startswith("ap:delete:"))
async def ap_delete(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    await delete_product(pid)
    await cb.message.edit_text("🗑 محصول حذف شد.")
    await cb.answer()


@router.callback_query(F.data.startswith("ap:publish:"))
async def ap_publish(cb: CallbackQuery, bot: Bot):
    pid = int(cb.data.split(":")[2])
    if not CHANNEL_ID:
        return await cb.answer("❌ CHANNEL_ID تنظیم نشده.", show_alert=True)
    await _publish(bot, pid)
    await cb.answer("✅ در کانال منتشر شد.", show_alert=True)


@router.callback_query(F.data.startswith("ap:price:"))
async def ap_edit_price(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[2])
    await state.update_data(edit_pid=pid, edit_field="price")
    await state.set_state(EditFSM.value)
    await cb.message.answer("💰 قیمت جدید (تومان):")
    await cb.answer()


@router.callback_query(F.data.startswith("ap:stock:"))
async def ap_edit_stock(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[2])
    await state.update_data(edit_pid=pid, edit_field="stock")
    await state.set_state(EditFSM.value)
    await cb.message.answer("📦 موجودی جدید:")
    await cb.answer()


@router.message(EditFSM.value)
async def edit_save(msg: Message, state: FSMContext):
    try:
        val = int(msg.text.strip().replace(",", "").replace("،", ""))
        assert val >= 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد صحیح وارد کنید:")
    data = await state.get_data()
    await update_product(data["edit_pid"], **{data["edit_field"]: val})
    await state.clear()
    await msg.answer("✅ ذخیره شد.", reply_markup=admin_menu())


# ─── orders ───────────────────────────────────────────────────────────────────
@router.message(F.text == "📋 سفارشات")
async def list_orders(msg: Message):
    orders = await get_all_orders()
    if not orders:
        return await msg.answer("📭 سفارشی وجود ندارد.")
    text = "📋 <b>سفارشات اخیر:</b>\n\n"
    icons = {"pending":"⏳","confirmed":"✅","shipped":"🚚","completed":"🎉","cancelled":"❌"}
    for o in orders[:20]:
        text += f"{icons.get(o['status'],'❓')} <b>#{o['id']}</b> — {o['product_title']} — {o['total_price']:,} تومان\n"
    await msg.answer(text)


@router.callback_query(F.data.startswith("os:"))
async def order_status_cb(cb: CallbackQuery, bot: Bot):
    _, new_status, oid_str = cb.data.split(":")
    oid = int(oid_str)
    order = await get_order(oid)
    if not order:
        return await cb.answer("سفارش یافت نشد.", show_alert=True)
    await set_order_status(oid, new_status)
    updated = await get_order(oid)
    label = STATUS_FA.get(new_status, new_status)
    try:
        await cb.message.edit_text(
            f"🔔 <b>سفارش #{oid}</b>\n\n" + admin_order_card(updated),
            reply_markup=order_action_kb(oid, new_status)
        )
    except Exception:
        pass
    await cb.answer(label, show_alert=True)
    user_msgs = {
        "confirmed": f"✅ سفارش <b>#{oid}</b> تأیید شد.",
        "shipped":   f"🚚 سفارش <b>#{oid}</b> ارسال شد.",
        "completed": f"🎉 سفارش <b>#{oid}</b> تکمیل شد. ممنون!",
        "cancelled": f"❌ سفارش <b>#{oid}</b> لغو شد.",
    }
    if new_status in user_msgs:
        try:
            await bot.send_message(order["user_tg_id"], user_msgs[new_status])
        except Exception:
            pass


# ─── reports ──────────────────────────────────────────────────────────────────
@router.message(F.text == "📊 گزارشات")
async def reports(msg: Message):
    stats = await sales_stats()
    best = await best_sellers()
    users = await count_users()
    text = (
        f"📊 <b>گزارش فروش:</b>\n\n"
        f"👥 کاربران: <b>{users}</b>\n"
        f"📦 کل سفارشات: <b>{stats.get('total', 0)}</b>\n"
        f"⏳ در انتظار: <b>{stats.get('pending', 0)}</b>\n"
        f"✅ فعال: <b>{stats.get('active', 0)}</b>\n"
        f"💰 درآمد کل: <b>{stats.get('revenue', 0):,} تومان</b>\n\n"
        f"🏆 <b>پرفروش‌ترین‌ها:</b>\n"
    )
    for i, b in enumerate(best, 1):
        text += f"{i}. {b['title']} — {b['cnt']} فروش — {b['rev']:,} تومان\n"
    await msg.answer(text)


@router.message(F.text == "⚙️ تنظیمات")
async def settings_msg(msg: Message):
    await msg.answer(
        f"⚙️ <b>تنظیمات:</b>\n\n"
        f"📢 کانال: <code>{CHANNEL_ID or 'تنظیم نشده'}</code>\n\n"
        "برای تغییر، مقدار <code>CHANNEL_ID</code> را در <code>.env</code> ویرایش کنید و ری‌استارت کنید."
    )
