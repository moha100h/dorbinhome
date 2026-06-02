from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu(is_admin=False):
    rows = [
        [KeyboardButton(text="🛍 فروشگاه"), KeyboardButton(text="📦 سفارش‌های من")],
        [KeyboardButton(text="❓ راهنما"), KeyboardButton(text="📞 پشتیبانی")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="👑 پنل مدیریت")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ محصول جدید"), KeyboardButton(text="📦 محصولات")],
        [KeyboardButton(text="🗂 دسته‌بندی‌ها"), KeyboardButton(text="🏷 برندها")],
        [KeyboardButton(text="🔧 کاربردها"), KeyboardButton(text="📋 سفارشات")],
        [KeyboardButton(text="📊 گزارشات"), KeyboardButton(text="⚙️ تنظیمات")],
        [KeyboardButton(text="🔙 منوی اصلی")],
    ], resize_keyboard=True)

def cancel_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ انصراف")]], resize_keyboard=True, one_time_keyboard=True)

def categories_kb(cats, parent_id=None):
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"📁 {c['name']}", callback_data=f"cat:{c['id']}")
    if parent_id is not None:
        b.button(text="🔙 بازگشت", callback_data=f"cat_back:{parent_id}")
    b.adjust(2)
    return b.as_markup()

def products_kb(products):
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "✅" if p["stock"] > 0 else "❌"
        b.button(text=f"{icon} {p['title']} — {p['price']:,} ت", callback_data=f"p:{p['id']}")
    b.button(text="🔙 دسته‌بندی‌ها", callback_data="shop")
    b.adjust(1)
    return b.as_markup()

def product_kb(pid, in_stock, cat_id=None):
    b = InlineKeyboardBuilder()
    if in_stock:
        b.button(text="🛒 خرید این محصول", callback_data=f"buy:{pid}")
    else:
        b.button(text="❌ ناموجود", callback_data="noop")
    back = f"cat:{cat_id}" if cat_id else "shop"
    b.button(text="🔙 بازگشت", callback_data=back)
    b.adjust(1)
    return b.as_markup()

def confirm_order_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ تأیید و ثبت سفارش", callback_data="order:confirm")
    b.button(text="✏️ ویرایش اطلاعات", callback_data="order:edit")
    b.button(text="❌ انصراف", callback_data="order:cancel")
    b.adjust(1)
    return b.as_markup()

def admin_products_kb(products):
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "🟢" if p["active"] else "🔴"
        b.button(text=f"{icon} {p['title']} | {p['stock']} عدد", callback_data=f"ap:view:{p['id']}")
    b.button(text="🔙 بازگشت", callback_data="admin:back")
    b.adjust(1)
    return b.as_markup()

def admin_product_kb(pid, active):
    b = InlineKeyboardBuilder()
    b.button(text="✏️ قیمت", callback_data=f"ap:price:{pid}")
    b.button(text="📦 موجودی", callback_data=f"ap:stock:{pid}")
    b.button(text="🔴 غیرفعال" if active else "🟢 فعال", callback_data=f"ap:toggle:{pid}")
    b.button(text="📢 کانال", callback_data=f"ap:publish:{pid}")
    b.button(text="🗑 حذف", callback_data=f"ap:delete:{pid}")
    b.button(text="🔙 بازگشت", callback_data="admin:products")
    b.adjust(2, 2, 1, 1)
    return b.as_markup()

def order_action_kb(oid, status):
    b = InlineKeyboardBuilder()
    if status == "pending":
        b.button(text="✅ تأیید", callback_data=f"os:confirmed:{oid}")
        b.button(text="❌ لغو", callback_data=f"os:cancelled:{oid}")
    elif status == "confirmed":
        b.button(text="🚚 ارسال شد", callback_data=f"os:shipped:{oid}")
        b.button(text="❌ لغو", callback_data=f"os:cancelled:{oid}")
    elif status == "shipped":
        b.button(text="🎉 تکمیل", callback_data=f"os:completed:{oid}")
    b.adjust(2)
    return b.as_markup()

def channel_product_kb(bot_username, pid):
    b = InlineKeyboardBuilder()
    b.button(text="🛒 خرید", url=f"https://t.me/{bot_username}?start=buy_{pid}")
    b.button(text="ℹ️ جزئیات", url=f"https://t.me/{bot_username}?start=p_{pid}")
    b.adjust(2)
    return b.as_markup()

def admin_list_kb(items, prefix):
    b = InlineKeyboardBuilder()
    for item in items:
        b.button(text=f"🗑 {item['name']}", callback_data=f"{prefix}:del:{item['id']}")
    b.button(text="🔙 بازگشت", callback_data="admin:back")
    b.adjust(1)
    return b.as_markup()

def select_category_kb(cats):
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"📁 {c['name']}", callback_data=f"sel_cat:{c['id']}")
    b.button(text="❌ انصراف", callback_data="ap_cancel")
    b.adjust(2)
    return b.as_markup()

def select_brand_kb(brands):
    b = InlineKeyboardBuilder()
    for br in brands:
        b.button(text=br["name"], callback_data=f"sel_brand:{br['id']}")
    b.button(text="➖ بدون برند", callback_data="sel_brand:0")
    b.button(text="❌ انصراف", callback_data="ap_cancel")
    b.adjust(2)
    return b.as_markup()

def select_usage_kb(usages):
    b = InlineKeyboardBuilder()
    for u in usages:
        b.button(text=u["name"], callback_data=f"sel_usage:{u['id']}")
    b.button(text="➖ بدون کاربرد", callback_data="sel_usage:0")
    b.button(text="❌ انصراف", callback_data="ap_cancel")
    b.adjust(2)
    return b.as_markup()

def done_images_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ اتمام ارسال عکس‌ها", callback_data="ap_images_done")
    b.button(text="❌ انصراف", callback_data="ap_cancel")
    b.adjust(1)
    return b.as_markup()

def settings_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📢 تغییر کانال", callback_data="set:channel")
    b.button(text="📞 تغییر پشتیبانی", callback_data="set:support")
    b.button(text="👋 ویرایش خوش‌آمد", callback_data="set:welcome")
    b.button(text="❓ ویرایش راهنما", callback_data="set:help")
    b.adjust(2)
    return b.as_markup()
