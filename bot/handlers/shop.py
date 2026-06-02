from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import aiosqlite
from database import DB
from keyboards import products_kb, product_detail_kb

router = Router()


async def get_products():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE active=1 ORDER BY id DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_product(product_id: int):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_product_images(product_id: int):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT file_id FROM product_images WHERE product_id=?", (product_id,)) as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def show_product(msg_or_cb, product_id: int):
    p = await get_product(product_id)
    if not p:
        text = "محصول یافت نشد."
        if hasattr(msg_or_cb, "answer"):
            await msg_or_cb.answer(text)
        else:
            await msg_or_cb.message.answer(text)
        return

    text = (
        f"📦 <b>{p['title']}</b>\n\n"
        f"{p['description'] or ''}\n\n"
        f"{'📋 مشخصات: ' + p['specs'] + chr(10) + chr(10) if p['specs'] else ''}"
        f"💰 قیمت: <b>{p['price']:,} تومان</b>\n"
        f"📊 موجودی: {'موجود ✅' if p['stock'] > 0 else 'ناموجود ❌'}"
    )
    kb = product_detail_kb(p["id"], p["stock"] > 0)
    images = await get_product_images(product_id)

    if hasattr(msg_or_cb, "answer"):
        if images:
            await msg_or_cb.answer_photo(photo=images[0], caption=text, reply_markup=kb)
        else:
            await msg_or_cb.answer(text, reply_markup=kb)
    else:
        if images:
            await msg_or_cb.message.answer_photo(photo=images[0], caption=text, reply_markup=kb)
        else:
            await msg_or_cb.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "shop:list")
async def shop_list(cb: CallbackQuery):
    products = await get_products()
    if not products:
        await cb.message.edit_text("📭 در حال حاضر محصولی موجود نیست.")
        return await cb.answer()
    await cb.message.edit_text("🛍 لیست محصولات:", reply_markup=products_kb(products))
    await cb.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_detail(cb: CallbackQuery):
    product_id = int(cb.data.split(":")[1])
    await show_product(cb, product_id)
    await cb.answer()
