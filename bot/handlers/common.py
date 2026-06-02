from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.db.repo import upsert_user, get_product, get_active_products, get_images
from bot.keyboards import main_menu, products_list_kb, product_kb
from bot.utils.fmt import product_card
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
                kb = product_kb(pid, p["stock"] > 0)
                if imgs:
                    await msg.answer_photo(imgs[0]["file_id"], caption=product_card(p), reply_markup=kb)
                else:
                    await msg.answer(product_card(p), reply_markup=kb)
                return
        except (ValueError, IndexError):
            pass

    await msg.answer(
        f"سلام <b>{msg.from_user.first_name}</b>! 👋\n"
        "به فروشگاه <b>دُربین‌هوم</b> خوش آمدید 🛍\n\n"
        "از منوی زیر انتخاب کنید:",
        reply_markup=main_menu(is_admin),
    )


@router.message(F.text == "🛍 فروشگاه")
async def shop_btn(msg: Message):
    products = await get_active_products()
    if not products:
        await msg.answer("📭 در حال حاضر محصولی موجود نیست.")
        return
    await msg.answer("🛍 <b>محصولات موجود:</b>", reply_markup=products_list_kb(products))


@router.callback_query(F.data == "shop")
async def shop_cb(cb: CallbackQuery):
    products = await get_active_products()
    if not products:
        await cb.message.edit_text("📭 در حال حاضر محصولی موجود نیست.")
        return await cb.answer()
    await cb.message.edit_text("🛍 <b>محصولات موجود:</b>", reply_markup=products_list_kb(products))
    await cb.answer()


@router.callback_query(F.data.startswith("p:"))
async def product_detail(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p:
        await cb.answer("محصول یافت نشد.", show_alert=True)
        return
    imgs = await get_images(pid)
    kb = product_kb(pid, p["stock"] > 0)
    text = product_card(p)
    if imgs:
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer_photo(imgs[0]["file_id"], caption=text, reply_markup=kb)
    else:
        await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "noop")
async def noop_cb(cb: CallbackQuery):
    await cb.answer("این محصول موجود نیست.", show_alert=True)
