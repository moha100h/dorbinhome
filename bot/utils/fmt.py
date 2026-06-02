STATUS_FA = {
    "pending":   "⏳ در انتظار تأیید",
    "confirmed": "✅ تأیید شده",
    "shipped":   "🚚 ارسال شده",
    "completed": "🎉 تکمیل شده",
    "cancelled": "❌ لغو شده",
}


def product_card(p: dict) -> str:
    lines = [f"<b>📦 {p['title']}</b>"]
    if p.get("description"):
        lines.append(f"\n{p['description']}")
    if p.get("specs"):
        lines.append(f"\n<b>📋 مشخصات:</b>\n{p['specs']}")
    lines.append(f"\n💰 قیمت: <b>{p['price']:,} تومان</b>")
    lines.append(f"📦 موجودی: {'✅ موجود' if p['stock'] > 0 else '❌ ناموجود'}")
    return "\n".join(lines)


def order_summary(data: dict, product: dict) -> str:
    return (
        f"🧾 <b>خلاصه سفارش:</b>\n\n"
        f"📦 {product['title']}\n"
        f"💰 {product['price']:,} تومان\n\n"
        f"👤 {data['full_name']}\n"
        f"📱 {data['phone']}\n"
        f"🗺 {data['province']} — {data['city']}\n"
        f"🏠 {data['address']}\n"
        f"📮 {data['postal_code']}\n\n"
        f"اطلاعات صحیح است؟"
    )


def order_card(o: dict) -> str:
    return (
        f"🧾 <b>سفارش #{o['id']}</b>\n"
        f"📦 {o['product_title']}\n"
        f"💰 {o['total_price']:,} تومان\n"
        f"وضعیت: {STATUS_FA.get(o['status'], o['status'])}\n"
        f"📅 {o['created_at'][:10]}"
    )


def admin_order_card(o: dict) -> str:
    return (
        f"📦 {o['product_title']}\n"
        f"💰 {o['total_price']:,} تومان\n\n"
        f"👤 {o['full_name']}\n"
        f"📱 {o['phone']}\n"
        f"🗺 {o['province']} — {o['city']}\n"
        f"🏠 {o['address']}\n"
        f"📮 {o['postal_code']}\n\n"
        f"وضعیت: {STATUS_FA.get(o['status'], o['status'])}"
    )
