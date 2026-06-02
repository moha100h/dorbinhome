STATUS_FA = {"pending":"⏳ در انتظار تأیید","confirmed":"✅ تأیید شده","shipped":"🚚 ارسال شده","completed":"🎉 تکمیل شده","cancelled":"❌ لغو شده"}

def product_card(p):
    lines = [f"<b>📦 {p['title']}</b>"]
    if p.get("brand_name"): lines.append(f"🏷 برند: {p['brand_name']}")
    if p.get("usage_name"): lines.append(f"🔧 کاربرد: {p['usage_name']}")
    if p.get("description"): lines.append(f"\n{p['description']}")
    if p.get("specs"): lines.append(f"\n<b>📋 مشخصات:</b>\n{p['specs']}")
    lines.append(f"\n💰 قیمت: <b>{p['price']:,} تومان</b>")
    lines.append(f"📊 موجودی: {'✅ موجود' if p['stock'] > 0 else '❌ ناموجود'}")
    return "\n".join(lines)

def order_summary(data, product):
    return (f"🧾 <b>خلاصه سفارش:</b>\n\n📦 {product['title']}\n💰 {product['price']:,} تومان\n\n"
            f"👤 {data['full_name']}\n📱 {data['phone']}\n🗺 {data['province']} — {data['city']}\n"
            f"🏠 {data['address']}\n📮 {data['postal_code']}\n\nاطلاعات صحیح است؟")

def order_card(o):
    return (f"🧾 <b>سفارش #{o['id']}</b>\n📦 {o['product_title']}\n"
            f"💰 {o['total_price']:,} تومان\nوضعیت: {STATUS_FA.get(o['status'],o['status'])}\n📅 {o['created_at'][:10]}")

def admin_order_card(o):
    return (f"📦 {o['product_title']}\n💰 {o['total_price']:,} تومان\n\n"
            f"👤 {o['full_name']}\n📱 {o['phone']}\n🗺 {o['province']} — {o['city']}\n"
            f"🏠 {o['address']}\n📮 {o['postal_code']}\n\nوضعیت: {STATUS_FA.get(o['status'],o['status'])}")
