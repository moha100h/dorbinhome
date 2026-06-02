from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.db.repo import (
    upsert_user, get_product, get_images, get_categories, get_category,
    get_products_by_category, get_user_by_tg, get_user_orders, get_setting
)
from bot.keyboards import main_menu, categories_kb, products_kb, product_kb
from bot.utils.fmt import product_card, order_card
from bot.core.config import ADMIN_ID

router = Router()

@router.message(CommandStart())
async def cmd_start(msg: Message):
    await upsert_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    is_admin = msg.from_user.id == ADMIN_ID
    arg = msg.text.split(maxsplit=1)[1] if " " in msg.text else ""
    if arg.startswith("p_"):
        try:
            pid = int(arg[2:])
            p = await get_product(pid)
            if p:
                imgs = await get_images(pid)
                kb = product_kb(pid, p["stock"] > 0, p.get("category_id"))
                if imgs:
                    await msg.answer_photo(imgs[0]["file_id"], caption=product_card(p), reply_markup=kb)
                else:
                    await msg.answer(product_card(p), reply_markup=kb)
                return
        except (ValueError, IndexError):
            pass
    welcome = await get_setting("welcome_text")
    await msg.answer(f"سلام <b>{msg.from_user.first_name}</b>! 👋\n{welcome}", reply_markup=main_menu(is_admin))

@router.message(F.text == "🛍 فروشگاه")
async def shop_btn(msg: Message):
    cats = await get_categories(None)
    if not cats:
        return await msg.answer("📭 در حال حاضر دسته‌بندی‌ای وجود ندارد.")
    await msg.answer("🛍 <b>دسته‌بندی‌ها:</b>", reply_markup=categories_kb(cats))

@router.callback_query(F.data == "shop")
async def shop_cb(cb: CallbackQuery):
    cats = await get_categories(None)
    if not cats:
        await cb.message.edit_text("📭 در حال حاضر دسته‌بندی‌ای وجود ندارد.")
        return await cb.answer()
    await cb.message.edit_text("🛍 <b>دسته‌بندی‌ها:</b>", reply_markup=categories_kb(cats))
    await cb.answer()

@router.callback_query(F.data.startswith("cat:"))
async def cat_cb(cb: CallbackQuery):
    cid = int(cb.data.split(":")[1])
    sub_cats = await get_categories(cid)
    if sub_cats:
        await cb.message.edit_text("📁 <b>زیردسته‌بندی‌ها:</b>", reply_markup=categories_kb(sub_cats, parent_id=cid))
        return await cb.answer()
    products = await get_products_by_category(cid)
    if not products:
        await cb.answer("📭 محصولی در این دسته وجود ندارد.", show_alert=True)
        return
    await cb.message.edit_text("📦 <b>محصولات:</b>", reply_markup=products_kb(products))
    await cb.answer()

@router.callback_query(F.data.startswith("cat_back:"))
async def cat_back_cb(cb: CallbackQuery):
    parent_id = int(cb.data.split(":")[1])
    parent = await get_category(parent_id)
    if parent and parent.get("parent_id"):
        cats = await get_categories(parent["parent_id"])
        await cb.message.edit_text("📁 <b>دسته‌بندی‌ها:</b>", reply_markup=categories_kb(cats, parent_id=parent["parent_id"]))
    else:
        cats = await get_categories(None)
        await cb.message.edit_text("🛍 <b>دسته‌بندی‌ها:</b>", reply_markup=categories_kb(cats))
    await cb.answer()

@router.callback_query(F.data.startswith("p:"))
async def product_detail(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("محصول یافت نشد.", show_alert=True)
        return
    imgs = await get_images(pid)
    kb = product_kb(pid, p["stock"] > 0, p.get("category_id"))
    text = product_card(p)
    if imgs:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer_photo(imgs[0]["file_id"], caption=text, reply_markup=kb)
    else:
        try:
            await cb.message.edit_text(text, reply_markup=kb)
        except Exception:
            await cb.message.answer(text, reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "noop")
async def noop_cb(cb: CallbackQuery):
    await cb.answer("این محصول موجود نیست.", show_alert=True)

@router.message(F.text == "📦 سفارش‌های من")
async def my_orders(msg: Message):
    user = await get_user_by_tg(msg.from_user.id)
    if not user:
        return await msg.answer("ابتدا /start بزنید.")
    orders = await get_user_orders(user["id"])
    if not orders:
        return await msg.answer("📭 هنوز سفارشی ثبت نکرده‌اید.")
    text = "📦 <b>سفارشات شما:</b>\n\n"
    for o in orders:
        text += order_card(o) + "\n" + "─" * 20 + "\n"
    await msg.answer(text)

@router.message(F.text == "❓ راهنما")
async def help_btn(msg: Message):
    text = await get_setting("help_text")
    await msg.answer(f"❓ <b>راهنما:</b>\n\n{text}")

@router.message(F.text == "📞 پشتیبانی")
async def support_btn(msg: Message):
    username = await get_setting("support_username")
    if username:
        await msg.answer(f"📞 <b>ارتباط با پشتیبانی:</b>\n\n👤 @{username.lstrip('@')}\n\nبرای ارتباط مستقیم روی آیدی بالا کلیک کنید.")
    else:
        await msg.answer("📞 در حال حاضر پشتیبانی تنظیم نشده است.")
