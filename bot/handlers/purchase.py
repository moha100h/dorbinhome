from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.db.repo import get_product, get_user_by_tg, create_order, get_order
from bot.keyboards import cancel_menu, main_menu, confirm_order_kb
from bot.utils.fmt import order_summary, admin_order_card
from bot.core.config import ADMIN_ID

router = Router()

class OrderFSM(StatesGroup):
    full_name = State(); phone = State(); province = State()
    city = State(); address = State(); postal_code = State(); confirm = State()

async def _cancel(msg, state):
    if msg.text == "❌ انصراف":
        await state.clear()
        await msg.answer("❌ سفارش لغو شد.", reply_markup=main_menu(msg.from_user.id == ADMIN_ID))
        return True
    return False

@router.callback_query(F.data.startswith("buy:"))
async def buy_start(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p or p["stock"] <= 0:
        await cb.answer("❌ این محصول موجود نیست.", show_alert=True); return
    await state.update_data(product_id=pid)
    await state.set_state(OrderFSM.full_name)
    await cb.message.answer(f"🛒 خرید: <b>{p['title']}</b>\n\n📝 <b>نام و نام خانوادگی:</b>", reply_markup=cancel_menu())
    await cb.answer()

@router.message(OrderFSM.full_name)
async def fsm_name(msg, state):
    if await _cancel(msg, state): return
    if len(msg.text.strip()) < 3: return await msg.answer("⚠️ نام باید حداقل ۳ کاراکتر باشد:")
    await state.update_data(full_name=msg.text.strip())
    await state.set_state(OrderFSM.phone)
    await msg.answer("📱 <b>شماره موبایل</b> (مثال: 09123456789):")

@router.message(OrderFSM.phone)
async def fsm_phone(msg, state):
    if await _cancel(msg, state): return
    p = msg.text.strip().replace(" ", "")
    if not (p.startswith("09") and len(p) == 11 and p.isdigit()):
        return await msg.answer("⚠️ شماره موبایل معتبر نیست:")
    await state.update_data(phone=p)
    await state.set_state(OrderFSM.province)
    await msg.answer("🗺 <b>استان:</b>")

@router.message(OrderFSM.province)
async def fsm_province(msg, state):
    if await _cancel(msg, state): return
    await state.update_data(province=msg.text.strip())
    await state.set_state(OrderFSM.city)
    await msg.answer("🏙 <b>شهر:</b>")

@router.message(OrderFSM.city)
async def fsm_city(msg, state):
    if await _cancel(msg, state): return
    await state.update_data(city=msg.text.strip())
    await state.set_state(OrderFSM.address)
    await msg.answer("🏠 <b>آدرس کامل:</b>")

@router.message(OrderFSM.address)
async def fsm_address(msg, state):
    if await _cancel(msg, state): return
    await state.update_data(address=msg.text.strip())
    await state.set_state(OrderFSM.postal_code)
    await msg.answer("📮 <b>کد پستی</b> (۱۰ رقم):")

@router.message(OrderFSM.postal_code)
async def fsm_postal(msg, state):
    if await _cancel(msg, state): return
    code = msg.text.strip().replace("-", "").replace(" ", "")
    if not (code.isdigit() and len(code) == 10):
        return await msg.answer("⚠️ کد پستی باید ۱۰ رقم باشد:")
    await state.update_data(postal_code=code)
    data = await state.get_data()
    p = await get_product(data["product_id"])
    if not p:
        await state.clear(); return await msg.answer("❌ محصول یافت نشد.")
    await state.set_state(OrderFSM.confirm)
    await msg.answer(order_summary(data, p), reply_markup=confirm_order_kb())

@router.callback_query(F.data == "order:confirm", OrderFSM.confirm)
async def order_confirm(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    p = await get_product(data["product_id"])
    if not p or p["stock"] <= 0:
        return await cb.message.edit_text("❌ متأسفانه موجودی تمام شد.")
    user = await get_user_by_tg(cb.from_user.id)
    if not user:
        return await cb.message.edit_text("❌ خطا: /start بزنید.")
    oid = await create_order(user_id=user["id"], product_id=p["id"], unit_price=p["price"],
        full_name=data["full_name"], phone=data["phone"], province=data["province"],
        city=data["city"], address=data["address"], postal_code=data["postal_code"])
    await cb.message.edit_text(f"✅ <b>سفارش #{oid} ثبت شد!</b>\n\n📦 {p['title']}\n💰 {p['price']:,} تومان\n\n⏳ پس از تأیید به شما اطلاع داده می‌شود.")
    order = await get_order(oid)
    from bot.keyboards import order_action_kb
    try:
        await bot.send_message(ADMIN_ID, f"🔔 <b>سفارش جدید #{oid}</b>\n\n" + admin_order_card(order), reply_markup=order_action_kb(oid, "pending"))
    except Exception:
        pass
    await cb.answer()

@router.callback_query(F.data == "order:edit", OrderFSM.confirm)
async def order_edit(cb: CallbackQuery, state: FSMContext):
    await state.set_state(OrderFSM.full_name)
    await cb.message.edit_text("✏️ از ابتدا وارد کنید.\n\n📝 <b>نام و نام خانوادگی:</b>")
    await cb.answer()

@router.callback_query(F.data == "order:cancel")
async def order_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ سفارش لغو شد.")
    await cb.answer()
