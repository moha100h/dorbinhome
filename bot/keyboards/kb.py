from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="🛍 فروشگاه"), KeyboardButton(text="📦 سفارش‌های من")]]
    if is_admin:
        rows.append([KeyboardButton(text="👑 پنل مدیریت")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ محصول جدید"), KeyboardButton(text="📦 محصولات")],
        [KeyboardButton(text="📋 سفارشات"),    KeyboardButton(text="📊 گزارشات")],
        [KeyboardButton(text="⚙️ تنظیمات"),   KeyboardButton(text="🔙 منوی اصلی")],
    ], resize_keyboard=True)


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ انصراف")]],
        resize_keyboard=True, one_time_keyboard=True
    )


def products_list_kb(products: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "✅" if p["stock"] > 0 else "❌"
        b.button(text=f"{icon} {p['title']} — {p['price']:,} تومان", callback_data=f"p:{p['id']}")
    b.adjust(1)
    return b.as_markup()


def product_kb(pid: int, in_stock: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if in_stock:
        b.button(text="🛒 خرید این محصول", callback_data=f"buy:{pid}")
    else:
        b.button(text="❌ ناموجود", callback_data="noop")
    b.button(text="🔙 بازگشت به لیست", callback_data="shop")
    b.adjust(1)
    return b.as_markup()


def confirm_order_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ تأیید و ثبت سفارش", callback_data="order:confirm")
    b.button(text="✏️ ویرایش اطلاعات",    callback_data="order:edit")
    b.button(text="❌ انصراف",             callback_data="order:cancel")
    b.adjust(1)
    return b.as_markup()


def admin_product_kb(pid: int, active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ ویرایش قیمت",   callback_data=f"ap:price:{pid}")
    b.button(text="📦 ویرایش موجودی", callback_data=f"ap:stock:{pid}")
    b.button(text="🔴 غیرفعال" if active else "🟢 فعال", callback_data=f"ap:toggle:{pid}")
    b.button(text="📢 انتشار کانال",  callback_data=f"ap:publish:{pid}")
    b.button(text="🗑 حذف",           callback_data=f"ap:delete:{pid}")
    b.button(text="🔙 بازگشت",        callback_data="admin:products")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def admin_products_kb(products: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "🟢" if p["active"] else "🔴"
        b.button(text=f"{icon} {p['title']} | موجودی: {p['stock']}", callback_data=f"ap:view:{p['id']}")
    b.button(text="🔙 بازگشت", callback_data="admin:back")
    b.adjust(1)
    return b.as_markup()


def order_action_kb(oid: int, status: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if status == "pending":
        b.button(text="✅ تأیید",    callback_data=f"os:confirmed:{oid}")
        b.button(text="❌ لغو",      callback_data=f"os:cancelled:{oid}")
    elif status == "confirmed":
        b.button(text="🚚 ارسال شد", callback_data=f"os:shipped:{oid}")
        b.button(text="❌ لغو",      callback_data=f"os:cancelled:{oid}")
    elif status == "shipped":
        b.button(text="🎉 تکمیل",   callback_data=f"os:completed:{oid}")
    b.adjust(2)
    return b.as_markup()


def channel_product_kb(bot_username: str, pid: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🛒 خرید",    url=f"https://t.me/{bot_username}?start=buy_{pid}")
    b.button(text="ℹ️ جزئیات", url=f"https://t.me/{bot_username}?start=p_{pid}")
    b.adjust(2)
    return b.as_markup()
