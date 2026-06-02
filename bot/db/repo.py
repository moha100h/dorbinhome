from __future__ import annotations
import aiosqlite
from bot.core.config import DB_PATH


async def _one(sql: str, p: tuple = ()) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, p) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def _all(sql: str, p: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, p) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def _run(sql: str, p: tuple = ()) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        cur = await db.execute(sql, p)
        await db.commit()
        return cur.lastrowid or 0


# users
async def upsert_user(tg_id: int, username: str | None, full_name: str | None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT INTO users (tg_id,username,full_name) VALUES (?,?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username,full_name=excluded.full_name",
            (tg_id, username, full_name)
        )
        await db.commit()
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as cur:
            return dict(await cur.fetchone())

async def get_user_by_tg(tg_id: int) -> dict | None:
    return await _one("SELECT * FROM users WHERE tg_id=?", (tg_id,))

async def get_user_by_id(uid: int) -> dict | None:
    return await _one("SELECT * FROM users WHERE id=?", (uid,))

async def count_users() -> int:
    r = await _one("SELECT COUNT(*) AS n FROM users")
    return r["n"] if r else 0


# products
async def create_product(title, description, specs, price, stock) -> int:
    return await _run(
        "INSERT INTO products (title,description,specs,price,stock) VALUES (?,?,?,?,?)",
        (title, description, specs, price, stock)
    )

async def get_product(pid: int) -> dict | None:
    return await _one("SELECT * FROM products WHERE id=?", (pid,))

async def get_active_products() -> list[dict]:
    return await _all("SELECT * FROM products WHERE active=1 AND stock>0 ORDER BY id DESC")

async def get_all_products() -> list[dict]:
    return await _all("SELECT * FROM products ORDER BY id DESC")

async def update_product(pid: int, **kw) -> None:
    if not kw: return
    sets = ", ".join(f"{k}=?" for k in kw)
    await _run(f"UPDATE products SET {sets} WHERE id=?", (*kw.values(), pid))

async def delete_product(pid: int) -> None:
    await _run("DELETE FROM products WHERE id=?", (pid,))

async def add_image(pid: int, file_id: str, order: int = 0) -> None:
    await _run("INSERT INTO product_images (product_id,file_id,sort_order) VALUES (?,?,?)", (pid, file_id, order))

async def get_images(pid: int) -> list[dict]:
    return await _all("SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order", (pid,))


# orders
async def create_order(user_id, product_id, unit_price, full_name, phone, province, city, address, postal_code) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        cur = await db.execute(
            "INSERT INTO orders (user_id,product_id,unit_price,total_price,full_name,phone,province,city,address,postal_code) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (user_id, product_id, unit_price, unit_price, full_name, phone, province, city, address, postal_code)
        )
        oid = cur.lastrowid
        await db.execute("UPDATE products SET stock=stock-1 WHERE id=? AND stock>0", (product_id,))
        await db.commit()
        return oid

async def get_order(oid: int) -> dict | None:
    return await _one(
        "SELECT o.*,p.title AS product_title,u.tg_id AS user_tg_id "
        "FROM orders o JOIN products p ON o.product_id=p.id JOIN users u ON o.user_id=u.id WHERE o.id=?",
        (oid,)
    )

async def get_user_orders(uid: int) -> list[dict]:
    return await _all(
        "SELECT o.*,p.title AS product_title FROM orders o "
        "JOIN products p ON o.product_id=p.id WHERE o.user_id=? ORDER BY o.id DESC LIMIT 20",
        (uid,)
    )

async def get_all_orders() -> list[dict]:
    return await _all(
        "SELECT o.*,p.title AS product_title,u.username FROM orders o "
        "JOIN products p ON o.product_id=p.id JOIN users u ON o.user_id=u.id ORDER BY o.id DESC LIMIT 50"
    )

async def set_order_status(oid: int, status: str) -> None:
    await _run("UPDATE orders SET status=? WHERE id=?", (status, oid))

async def sales_stats() -> dict:
    r = await _one(
        "SELECT COUNT(*) AS total, COALESCE(SUM(total_price),0) AS revenue, "
        "SUM(status='pending') AS pending, "
        "SUM(status IN ('confirmed','shipped','completed')) AS active FROM orders"
    )
    return r or {}

async def best_sellers(limit: int = 5) -> list[dict]:
    return await _all(
        "SELECT p.title,COUNT(o.id) AS cnt,SUM(o.total_price) AS rev "
        "FROM orders o JOIN products p ON o.product_id=p.id "
        "WHERE o.status!='cancelled' GROUP BY p.id ORDER BY cnt DESC LIMIT ?",
        (limit,)
    )
