from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🛍 مشاهده محصولات", callback_data="shop:list")],
        [InlineKeyboardButton(text="📦 سفارش‌های من", callback_data="my:orders")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="👑 پنل مدیریت", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"📦 {p['title']} — {p['price']:,} تومان",
            callback_data=f"product:{p['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product_id: int, in_stock: bool) -> InlineKeyboardMarkup:
    buttons = []
    if in_stock:
        buttons.append([InlineKeyboardButton(text="🛒 خرید", callback_data=f"buy:{product_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="❌ ناموجود", callback_data="noop")])
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن محصول", callback_data="admin:add_product")],
        [InlineKeyboardButton(text="📦 لیست محصولات", callback_data="admin:products")],
        [InlineKeyboardButton(text="📋 سفارشات", callback_data="admin:orders")],
        [InlineKeyboardButton(text="📊 گزارش فروش", callback_data="admin:report")],
        [InlineKeyboardButton(text="⚙️ تنظیمات کانال", callback_data="admin:channel")],
        [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="back:main")],
    ])


def order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data=f"order:confirm:{order_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"order:reject:{order_id}"),
        ],
        [InlineKeyboardButton(text="🚚 ارسال شد", callback_data=f"order:ship:{order_id}")],
    ])


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ انصراف")]],
        resize_keyboard=True, one_time_keyboard=True
    )


def channel_product_kb(bot_username: str, product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 خرید", url=f"https://t.me/{bot_username}?start=buy_{product_id}")],
        [InlineKeyboardButton(text="ℹ️ جزئیات", url=f"https://t.me/{bot_username}?start=product_{product_id}")],
    ])
