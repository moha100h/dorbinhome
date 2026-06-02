from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter, Command
from bot.db.repo import (
    create_product, get_all_products, get_product, update_product, delete_product,
    add_image, get_images, get_all_orders, set_order_status, get_order,
    sales_stats, best_sellers, count_users,
    get_categories, get_category, create_category, delete_category,
    get_brands, create_brand, delete_brand,
    get_usages, create_usage, delete_usage,
    get_setting, set_setting,
)
from bot.keyboards import (
    admin_menu, main_menu, admin_products_kb, admin_product_kb,
    order_action_kb, channel_product_kb, admin_list_kb,
    select_category_kb, select_brand_kb, select_usage_kb,
    done_images_kb, settings_kb,
)
from bot.utils.fmt import admin_order_card, STATUS_FA
from bot.core.config import ADMIN_ID

router = Router()

class AdminFilter(Filter):
    async def __call__(self, event) -> bool:
        uid = getattr(getattr(event, "from_user", None), "id", None)
        return uid == ADMIN_ID

router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

class AddProductFSM(StatesGroup):
    category = State(); brand = State(); usage = State()
    title = State(); desc = State(); specs = State()
    price = State(); stock = State(); images = State()

class EditFSM(StatesGroup):
    value = State()

class AddCatFSM(StatesGroup):
    name = State()

class AddSimpleFSM(StatesGroup):
    name = State()

class SettingFSM(StatesGroup):
    value = State()

@router.message(F.text == "👑 پنل مدیریت")
async def admin_panel(msg: Message):
    await msg.answer("👑 <b>پنل مدیریت:</b>", reply_markup=admin_menu())

@router.message(F.text == "🔙 منوی اصلی")
async def back_main(msg: Message):
    await msg.answer("منوی اصلی:", reply_markup=main_menu(True))

@router.callback_query(F.data == "admin:back")
async def admin_back(cb: CallbackQuery):
    await cb.message.edit_text("👑 <b>پنل مدیریت:</b>")
    await cb.answer()

@router.callback_query(F.data == "admin:products")
async def admin_products_cb(cb: CallbackQuery):
    products = await get_all_products()
    if not products:
        await cb.message.edit_text("📭 محصولی وجود ندارد.")
        return await cb.answer()
    await cb.message.edit_text("📦 <b>لیست محصولات:</b>", reply_markup=admin_products_kb(products))
    await cb.answer()

@router.message(F.text == "➕ محصول جدید")
async def add_product_start(msg: Message, state: FSMContext):
    cats = await get_categories(None)
    if not cats:
        return await msg.answer("⚠️ ابتدا از 🗂 دسته‌بندی‌ها یک دسته بسازید.")
    await state.set_state(AddProductFSM.category)
    await msg.answer("📁 <b>دسته‌بندی محصول:</b>", reply_markup=select_category_kb(cats))

@router.callback_query(F.data == "ap_cancel")
async def ap_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ لغو شد.")
    await cb.answer()

@router.callback_query(F.data.startswith("sel_cat:"), AddProductFSM.category)
async def ap_sel_cat(cb: CallbackQuery, state: FSMContext):
    cid = int(cb.data.split(":")[1])
    sub = await get_categories(cid)
    if sub:
        await cb.message.edit_text("📁 <b>زیردسته:</b>", reply_markup=select_category_kb(sub))
        return await cb.answer()
    await state.update_data(category_id=cid)
    await state.set_state(AddProductFSM.brand)
    brands = await get_brands()
    await cb.message.edit_text("🏷 <b>برند محصول:</b>", reply_markup=select_brand_kb(brands))
    await cb.answer()

@router.callback_query(F.data.startswith("sel_brand:"), AddProductFSM.brand)
async def ap_sel_brand(cb: CallbackQuery, state: FSMContext):
    bid = int(cb.data.split(":")[1])
    await state.update_data(brand_id=bid if bid else None)
    await state.set_state(AddProductFSM.usage)
    usages = await get_usages()
    await cb.message.edit_text("🔧 <b>کاربرد محصول:</b>", reply_markup=select_usage_kb(usages))
    await cb.answer()

@router.callback_query(F.data.startswith("sel_usage:"), AddProductFSM.usage)
async def ap_sel_usage(cb: CallbackQuery, state: FSMContext):
    uid = int(cb.data.split(":")[1])
    await state.update_data(usage_id=uid if uid else None)
    await state.set_state(AddProductFSM.title)
    await cb.message.answer("📝 <b>عنوان محصول:</b>")
    await cb.answer()

@router.message(AddProductFSM.title)
async def ap_title(msg: Message, state: FSMContext):
    if len(msg.text.strip()) < 2: return await msg.answer("⚠️ عنوان خیلی کوتاه:")
    await state.update_data(title=msg.text.strip())
    await state.set_state(AddProductFSM.desc)
    await msg.answer("📄 <b>توضیحات</b> (یا - برای رد):")

@router.message(AddProductFSM.desc)
async def ap_desc(msg: Message, state: FSMContext):
    await state.update_data(description=None if msg.text.strip()=="-" else msg.text.strip())
    await state.set_state(AddProductFSM.specs)
    await msg.answer("📋 <b>مشخصات فنی</b> (یا - برای رد):")

@router.message(AddProductFSM.specs)
async def ap_specs(msg: Message, state: FSMContext):
    await state.update_data(specs=None if msg.text.strip()=="-" else msg.text.strip())
    await state.set_state(AddProductFSM.price)
    await msg.answer("💰 <b>قیمت</b> (تومان):")

@router.message(AddProductFSM.price)
async def ap_price(msg: Message, state: FSMContext):
    try:
        price = int(msg.text.strip().replace(",","").replace("،","")); assert price > 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد مثبت وارد کنید:")
    await state.update_data(price=price)
    await state.set_state(AddProductFSM.stock)
    await msg.answer("📦 <b>تعداد موجودی:</b>")

@router.message(AddProductFSM.stock)
async def ap_stock(msg: Message, state: FSMContext):
    try:
        stock = int(msg.text.strip()); assert stock >= 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد غیرمنفی وارد کنید:")
    await state.update_data(stock=stock, images=[])
    await state.set_state(AddProductFSM.images)
    await msg.answer("🖼 <b>تصاویر محصول</b> را ارسال کنید.\nپس از اتمام دکمه زیر را بزنید 👇", reply_markup=done_images_kb())

@router.message(AddProductFSM.images, F.photo)
async def ap_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    imgs = data.get("images", [])
    imgs.append(msg.photo[-1].file_id)
    await state.update_data(images=imgs)
    await msg.answer(f"✅ عکس {len(imgs)} دریافت شد 👇", reply_markup=done_images_kb())

@router.callback_query(F.data == "ap_images_done", AddProductFSM.images)
async def ap_images_done(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    pid = await create_product(
        category_id=data.get("category_id"), brand_id=data.get("brand_id"),
        usage_id=data.get("usage_id"), title=data["title"],
        description=data.get("description"), specs=data.get("specs"),
        price=data["price"], stock=data["stock"])
    for i, fid in enumerate(data.get("images", [])):
        await add_image(pid, fid, i)
    await cb.message.edit_text(f"✅ محصول <b>#{pid} — {data['title']}</b> اضافه شد!")
    await cb.message.answer("👑 <b>پنل مدیریت:</b>", reply_markup=admin_menu())
    channel_id = await get_setting("channel_id")
    if channel_id:
        await _publish(bot, pid, channel_id)
        await cb.message.answer("📢 محصول در کانال منتشر شد.")
    await cb.answer()

async def _publish(bot, pid, channel_id):
    p = await get_product(pid)
    imgs = await get_images(pid)
    me = await bot.get_me()
    kb = channel_product_kb(me.username, pid)
    caption = (f"📦 <b>{p['title']}</b>\n\n{p['description'] or ''}\n\n"
               f"{'📋 ' + p['specs'] + chr(10) if p.get('specs') else ''}"
               f"💰 قیمت: <b>{p['price']:,} تومان</b>\n📊 موجودی: {p['stock']} عدد")
    try:
        if imgs:
            sent = await bot.send_photo(channel_id, imgs[0]["file_id"], caption=caption, reply_markup=kb)
        else:
            sent = await bot.send_message(channel_id, caption, reply_markup=kb)
        await update_product(pid, channel_msg_id=sent.message_id)
    except Exception:
        pass

@router.message(F.text == "📦 محصولات")
async def list_products(msg: Message):
    products = await get_all_products()
    if not products: return await msg.answer("📭 محصولی وجود ندارد.")
    await msg.answer("📦 <b>لیست محصولات:</b>", reply_markup=admin_products_kb(products))

@router.callback_query(F.data.startswith("ap:view:"))
async def ap_view(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    p = await get_product(pid)
    if not p: return await cb.answer("یافت نشد.", show_alert=True)
    text = (f"📦 <b>{p['title']}</b>\n💰 {p['price']:,} ت | 📊 {p['stock']} عدد\n"
            f"{'🟢 فعال' if p['active'] else '🔴 غیرفعال'} | "
            f"{'📢 در کانال' if p['channel_msg_id'] else '📭 منتشر نشده'}")
    await cb.message.edit_text(text, reply_markup=admin_product_kb(pid, bool(p["active"])))
    await cb.answer()

@router.callback_query(F.data.startswith("ap:toggle:"))
async def ap_toggle(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    p = await get_product(pid)
    new = 0 if p["active"] else 1
    await update_product(pid, active=new)
    await cb.answer(f"{'🟢 فعال' if new else '🔴 غیرفعال'} شد.", show_alert=True)
    p2 = await get_product(pid)
    await cb.message.edit_text(
        f"📦 <b>{p2['title']}</b>\n💰 {p2['price']:,} ت | 📊 {p2['stock']} عدد\n{'🟢 فعال' if p2['active'] else '🔴 غیرفعال'}",
        reply_markup=admin_product_kb(pid, bool(p2["active"])))

@router.callback_query(F.data.startswith("ap:delete:"))
async def ap_delete(cb: CallbackQuery):
    pid = int(cb.data.split(":")[2])
    await delete_product(pid)
    await cb.message.edit_text("🗑 محصول حذف شد.")
    await cb.answer()

@router.callback_query(F.data.startswith("ap:publish:"))
async def ap_publish(cb: CallbackQuery, bot: Bot):
    pid = int(cb.data.split(":")[2])
    channel_id = await get_setting("channel_id")
    if not channel_id:
        return await cb.answer("❌ کانال تنظیم نشده.", show_alert=True)
    await _publish(bot, pid, channel_id)
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
        val = int(msg.text.strip().replace(",","").replace("،","")); assert val >= 0
    except (ValueError, AssertionError):
        return await msg.answer("⚠️ عدد معتبر وارد کنید:")
    data = await state.get_data()
    await update_product(data["edit_pid"], **{data["edit_field"]: val})
    await state.clear()
    await msg.answer("✅ ذخیره شد.", reply_markup=admin_menu())

@router.message(F.text == "🗂 دسته‌بندی‌ها")
async def cats_menu(msg: Message, state: FSMContext):
    await state.set_state(AddCatFSM.name)
    cats = await get_categories(None)
    lines = ["🗂 <b>دسته‌بندی‌های فعلی:</b>\n"]
    for c in cats:
        sub = await get_categories(c["id"])
        lines.append(f"📁 {c['name']}" + (f" ← {', '.join(s['name'] for s in sub)}" if sub else ""))
    lines += ["\n📝 نام دسته جدید را بفرستید:", "<i>برای زیردسته: <code>والد > زیردسته</code></i>", "برای حذف: /delcat"]
    await msg.answer("\n".join(lines))

@router.message(AddCatFSM.name)
async def add_cat(msg: Message, state: FSMContext):
    await state.clear()
    text = msg.text.strip()
    if ">" in text:
        parts = [p.strip() for p in text.split(">", 1)]
        parent_name, child_name = parts[0], parts[1]
        cats = await get_categories(None)
        parent = next((c for c in cats if c["name"] == parent_name), None)
        parent_id = parent["id"] if parent else await create_category(parent_name)
        await create_category(child_name, parent_id)
        await msg.answer(f"✅ زیردسته <b>{child_name}</b> زیر <b>{parent_name}</b> ایجاد شد.", reply_markup=admin_menu())
    else:
        await create_category(text)
        await msg.answer(f"✅ دسته‌بندی <b>{text}</b> ایجاد شد.", reply_markup=admin_menu())

@router.message(Command("delcat"))
async def delcat_cmd(msg: Message):
    cats = await get_categories(None)
    all_cats = []
    for c in cats:
        all_cats.append(c)
        all_cats.extend(await get_categories(c["id"]))
    if not all_cats: return await msg.answer("دسته‌بندی‌ای وجود ندارد.")
    await msg.answer("🗑 کدام دسته را حذف کنیم؟", reply_markup=admin_list_kb(all_cats, "cat"))

@router.callback_query(F.data.startswith("cat:del:"))
async def del_cat_cb(cb: CallbackQuery):
    cid = int(cb.data.split(":")[2])
    await delete_category(cid)
    await cb.message.edit_text("🗑 دسته‌بندی حذف شد.")
    await cb.answer()

@router.message(F.text == "🏷 برندها")
async def brands_menu(msg: Message, state: FSMContext):
    await state.update_data(item_type="brand")
    await state.set_state(AddSimpleFSM.name)
    brands = await get_brands()
    text = "🏷 <b>برندها:</b>\n" + ("\n".join(f"• {b['name']}" for b in brands) or "هنوز برندی وجود ندارد.")
    await msg.answer(text + "\n\n📝 نام برند جدید:\nبرای حذف: /delbrand")

@router.message(F.text == "🔧 کاربردها")
async def usages_menu(msg: Message, state: FSMContext):
    await state.update_data(item_type="usage")
    await state.set_state(AddSimpleFSM.name)
    usages = await get_usages()
    text = "🔧 <b>کاربردها:</b>\n" + ("\n".join(f"• {u['name']}" for u in usages) or "هنوز کاربردی وجود ندارد.")
    await msg.answer(text + "\n\n📝 نام کاربرد جدید:\nبرای حذف: /delusage")

@router.message(AddSimpleFSM.name)
async def add_simple_item(msg: Message, state: FSMContext):
    data = await state.get_data()
    item_type = data.get("item_type", "brand")
    await state.clear()
    name = msg.text.strip()
    if item_type == "brand":
        await create_brand(name)
        await msg.answer(f"✅ برند <b>{name}</b> اضافه شد.", reply_markup=admin_menu())
    else:
        await create_usage(name)
        await msg.answer(f"✅ کاربرد <b>{name}</b> اضافه شد.", reply_markup=admin_menu())

@router.message(Command("delbrand"))
async def delbrand_cmd(msg: Message):
    brands = await get_brands()
    if not brands: return await msg.answer("برندی وجود ندارد.")
    await msg.answer("🗑 کدام برند را حذف کنیم؟", reply_markup=admin_list_kb(brands, "brand"))

@router.message(Command("delusage"))
async def delusage_cmd(msg: Message):
    usages = await get_usages()
    if not usages: return await msg.answer("کاربردی وجود ندارد.")
    await msg.answer("🗑 کدام کاربرد را حذف کنیم؟", reply_markup=admin_list_kb(usages, "usage"))

@router.callback_query(F.data.startswith("brand:del:"))
async def del_brand_cb(cb: CallbackQuery):
    bid = int(cb.data.split(":")[2])
    await delete_brand(bid)
    await cb.message.edit_text("🗑 برند حذف شد.")
    await cb.answer()

@router.callback_query(F.data.startswith("usage:del:"))
async def del_usage_cb(cb: CallbackQuery):
    uid = int(cb.data.split(":")[2])
    await delete_usage(uid)
    await cb.message.edit_text("🗑 کاربرد حذف شد.")
    await cb.answer()

@router.message(F.text == "📋 سفارشات")
async def list_orders(msg: Message):
    orders = await get_all_orders()
    if not orders: return await msg.answer("📭 سفارشی وجود ندارد.")
    icons = {"pending":"⏳","confirmed":"✅","shipped":"🚚","completed":"🎉","cancelled":"❌"}
    text = "📋 <b>سفارشات اخیر:</b>\n\n"
    for o in orders[:20]:
        text += f"{icons.get(o['status'],'❓')} <b>#{o['id']}</b> — {o['product_title']} — {o['total_price']:,} ت — {o['full_name']}\n"
    await msg.answer(text)

@router.callback_query(F.data.startswith("os:"))
async def order_status_cb(cb: CallbackQuery, bot: Bot):
    _, new_status, oid_str = cb.data.split(":")
    oid = int(oid_str)
    order = await get_order(oid)
    if not order: return await cb.answer("سفارش یافت نشد.", show_alert=True)
    await set_order_status(oid, new_status)
    updated = await get_order(oid)
    try:
        await cb.message.edit_text(f"🔔 <b>سفارش #{oid}</b>\n\n" + admin_order_card(updated), reply_markup=order_action_kb(oid, new_status))
    except Exception:
        pass
    await cb.answer(STATUS_FA.get(new_status, new_status), show_alert=True)
    user_msgs = {"confirmed": f"✅ سفارش <b>#{oid}</b> تأیید شد.", "shipped": f"🚚 سفارش <b>#{oid}</b> ارسال شد.", "completed": f"🎉 سفارش <b>#{oid}</b> تکمیل شد.", "cancelled": f"❌ سفارش <b>#{oid}</b> لغو شد."}
    if new_status in user_msgs:
        try:
            await bot.send_message(order["user_tg_id"], user_msgs[new_status])
        except Exception:
            pass

@router.message(F.text == "📊 گزارشات")
async def reports(msg: Message):
    stats = await sales_stats()
    best = await best_sellers()
    users = await count_users()
    text = (f"📊 <b>گزارش فروش:</b>\n\n👥 کاربران: <b>{users}</b>\n"
            f"📦 کل سفارشات: <b>{stats.get('total',0)}</b>\n⏳ در انتظار: <b>{stats.get('pending',0)}</b>\n"
            f"✅ فعال: <b>{stats.get('active',0)}</b>\n💰 درآمد کل: <b>{stats.get('revenue',0):,} تومان</b>\n\n🏆 <b>پرفروش‌ترین‌ها:</b>\n")
    for i, b in enumerate(best, 1):
        text += f"{i}. {b['title']} — {b['cnt']} فروش — {b['rev']:,} ت\n"
    await msg.answer(text)

@router.message(F.text == "⚙️ تنظیمات")
async def settings_view(msg: Message):
    channel = await get_setting("channel_id")
    support = await get_setting("support_username")
    welcome = await get_setting("welcome_text")
    help_t  = await get_setting("help_text")
    text = (f"⚙️ <b>تنظیمات فعلی:</b>\n\n📢 کانال: <code>{channel or 'تنظیم نشده'}</code>\n"
            f"📞 پشتیبانی: <code>{support or 'تنظیم نشده'}</code>\n"
            f"👋 خوش‌آمد: {welcome[:60]}...\n❓ راهنما: {help_t[:60]}...\n\nبرای تغییر دکمه مورد نظر را بزنید:")
    await msg.answer(text, reply_markup=settings_kb())

@router.callback_query(F.data.startswith("set:"))
async def settings_cb(cb: CallbackQuery, state: FSMContext):
    key_map = {
        "set:channel": ("channel_id",      "📢 آیدی کانال جدید:\n<i>مثال: @mychannel یا -1001234567890</i>"),
        "set:support": ("support_username", "📞 یوزرنیم پشتیبانی:\n<i>مثال: support_user (بدون @)</i>"),
        "set:welcome": ("welcome_text",     "👋 متن خوش‌آمد جدید:"),
        "set:help":    ("help_text",        "❓ متن راهنمای جدید:"),
    }
    if cb.data not in key_map: return await cb.answer()
    setting_key, prompt = key_map[cb.data]
    await state.update_data(setting_key=setting_key)
    await state.set_state(SettingFSM.value)
    await cb.message.answer(prompt)
    await cb.answer()

@router.message(SettingFSM.value)
async def setting_save(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await set_setting(data["setting_key"], msg.text.strip())
    await msg.answer("✅ تنظیم ذخیره شد.", reply_markup=admin_menu())
