from __future__ import annotations
import aiosqlite
from bot.core.config import DB_PATH

async def _one(sql, p=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, p) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def _all(sql, p=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, p) as c:
            return [dict(r) for r in await c.fetchall()]

async def _run(sql, p=()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        c = await db.execute(sql, p)
        await db.commit()
        return c.lastrowid or 0

async def get_setting(key):
    r = await _one("SELECT value FROM settings WHERE key=?", (key,))
    return r["value"] if r else ""

async def set_setting(key, value):
    await _run("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

async def upsert_user(tg_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("INSERT INTO users(tg_id,username,full_name) VALUES(?,?,?) ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username,full_name=excluded.full_name", (tg_id, username, full_name))
        await db.commit()
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as c:
            return dict(await c.fetchone())

async def get_user_by_tg(tg_id):
    return await _one("SELECT * FROM users WHERE tg_id=?", (tg_id,))

async def count_users():
    r = await _one("SELECT COUNT(*) n FROM users")
    return r["n"] if r else 0

async def get_categories(parent_id=None):
    if parent_id is None:
        return await _all("SELECT * FROM categories WHERE parent_id IS NULL ORDER BY sort_order,name")
    return await _all("SELECT * FROM categories WHERE parent_id=? ORDER BY sort_order,name", (parent_id,))

async def get_category(cid):
    return await _one("SELECT * FROM categories WHERE id=?", (cid,))

async def create_category(name, parent_id=None):
    return await _run("INSERT INTO categories(name,parent_id) VALUES(?,?)", (name, parent_id))

async def delete_category(cid):
    await _run("DELETE FROM categories WHERE id=?", (cid,))

async def get_brands():
    return await _all("SELECT * FROM brands ORDER BY name")

async def create_brand(name):
    return await _run("INSERT OR IGNORE INTO brands(name) VALUES(?)", (name,))

async def delete_brand(bid):
    await _run("DELETE FROM brands WHERE id=?", (bid,))

async def get_usages():
    return await _all("SELECT * FROM usages ORDER BY name")

async def create_usage(name):
    return await _run("INSERT OR IGNORE INTO usages(name) VALUES(?)", (name,))

async def delete_usage(uid):
    await _run("DELETE FROM usages WHERE id=?", (uid,))

async def create_product(category_id, brand_id, usage_id, title, description, specs, price, stock):
    return await _run("INSERT INTO products(category_id,brand_id,usage_id,title,description,specs,price,stock) VALUES(?,?,?,?,?,?,?,?)", (category_id, brand_id, usage_id, title, description, specs, price, stock))

async def get_product(pid):
    return await _one("SELECT p.*,c.name AS category_name,b.name AS brand_name,u.name AS usage_name FROM products p LEFT JOIN categories c ON p.category_id=c.id LEFT JOIN brands b ON p.brand_id=b.id LEFT JOIN usages u ON p.usage_id=u.id WHERE p.id=?", (pid,))

async def get_products_by_category(cid):
    return await _all("SELECT p.*,b.name AS brand_name,u.name AS usage_name FROM products p LEFT JOIN brands b ON p.brand_id=b.id LEFT JOIN usages u ON p.usage_id=u.id WHERE p.category_id=? AND p.active=1 AND p.stock>0 ORDER BY p.id DESC", (cid,))

async def get_all_products():
    return await _all("SELECT p.*,c.name AS category_name,b.name AS brand_name FROM products p LEFT JOIN categories c ON p.category_id=c.id LEFT JOIN brands b ON p.brand_id=b.id ORDER BY p.id DESC")

async def update_product(pid, **kw):
    if not kw: return
    sets = ", ".join(f"{k}=?" for k in kw)
    await _run(f"UPDATE products SET {sets} WHERE id=?", (*kw.values(), pid))

async def delete_product(pid):
    await _run("DELETE FROM products WHERE id=?", (pid,))

async def add_image(pid, file_id, order=0):
    await _run("INSERT INTO product_images(product_id,file_id,sort_order) VALUES(?,?,?)", (pid, file_id, order))

async def get_images(pid):
    return await _all("SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order", (pid,))

async def create_order(user_id, product_id, unit_price, full_name, phone, province, city, address, postal_code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        c = await db.execute("INSERT INTO orders(user_id,product_id,unit_price,total_price,full_name,phone,province,city,address,postal_code) VALUES(?,?,?,?,?,?,?,?,?,?)", (user_id, product_id, unit_price, unit_price, full_name, phone, province, city, address, postal_code))
        oid = c.lastrowid
        await db.execute("UPDATE products SET stock=stock-1 WHERE id=? AND stock>0", (product_id,))
        await db.commit()
        return oid

async def get_order(oid):
    return await _one("SELECT o.*,p.title AS product_title,u.tg_id AS user_tg_id FROM orders o JOIN products p ON o.product_id=p.id JOIN users u ON o.user_id=u.id WHERE o.id=?", (oid,))

async def get_user_orders(uid):
    return await _all("SELECT o.*,p.title AS product_title FROM orders o JOIN products p ON o.product_id=p.id WHERE o.user_id=? ORDER BY o.id DESC LIMIT 20", (uid,))

async def get_all_orders(status=None):
    if status:
        return await _all("SELECT o.*,p.title AS product_title,u.full_name AS user_full_name FROM orders o JOIN products p ON o.product_id=p.id JOIN users u ON o.user_id=u.id WHERE o.status=? ORDER BY o.id DESC LIMIT 50", (status,))
    return await _all("SELECT o.*,p.title AS product_title,u.full_name AS user_full_name FROM orders o JOIN products p ON o.product_id=p.id JOIN users u ON o.user_id=u.id ORDER BY o.id DESC LIMIT 50")

async def set_order_status(oid, status):
    await _run("UPDATE orders SET status=? WHERE id=?", (status, oid))

async def sales_stats():
    r = await _one("SELECT COUNT(*) AS total, COALESCE(SUM(total_price),0) AS revenue, SUM(status='pending') AS pending, SUM(status IN ('confirmed','shipped','completed')) AS active FROM orders")
    return r or {}

async def best_sellers(limit=5):
    return await _all("SELECT p.title,COUNT(o.id) AS cnt,SUM(o.total_price) AS rev FROM orders o JOIN products p ON o.product_id=p.id WHERE o.status!='cancelled' GROUP BY p.id ORDER BY cnt DESC LIMIT ?", (limit,))
