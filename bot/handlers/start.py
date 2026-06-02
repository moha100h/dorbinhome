from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
import aiosqlite
from config import config
from keyboards import main_menu
from database import DB

router = Router()


async def upsert_user(tg_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            INSERT INTO users (tg_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
        """, (tg_id, username, full_name))
        await db.commit()


@router.message(CommandStart())
async def cmd_start(msg: Message):
    await upsert_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.full_name or "")
    is_admin = msg.from_user.id == config.ADMIN_ID
    arg = msg.text.split()[-1] if len(msg.text.split()) > 1 else ""

    if arg.startswith("product_"):
        from handlers.shop import show_product
        product_id = int(arg.split("_")[1])
        await show_product(msg, product_id)
        return
    if arg.startswith("buy_"):
        product_id = int(arg.split("_")[1])
        await msg.answer(f"برای خرید محصول #{product_id} روی دکمه زیر کلیک کنید:", reply_markup=main_menu(is_admin))
        return

    await msg.answer(
        f"سلام {msg.from_user.first_name}! 👋\nبه فروشگاه ما خوش آمدید.\n\nاز منوی زیر انتخاب کنید:",
        reply_markup=main_menu(is_admin)
    )


@router.callback_query(F.data == "back:main")
async def back_main(cb: CallbackQuery):
    is_admin = cb.from_user.id == config.ADMIN_ID
    await cb.message.edit_text("منوی اصلی:", reply_markup=main_menu(is_admin))
    await cb.answer()


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer("این محصول موجود نیست.", show_alert=True)
