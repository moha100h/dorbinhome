import aiosqlite
from bot.core.config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id       INTEGER UNIQUE NOT NULL,
                username    TEXT,
                full_name   TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                description     TEXT,
                specs           TEXT,
                price           INTEGER NOT NULL CHECK(price > 0),
                stock           INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                active          INTEGER NOT NULL DEFAULT 1,
                channel_msg_id  INTEGER,
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS product_images (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                file_id     TEXT NOT NULL,
                sort_order  INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                product_id   INTEGER NOT NULL REFERENCES products(id),
                unit_price   INTEGER NOT NULL,
                total_price  INTEGER NOT NULL,
                status       TEXT NOT NULL DEFAULT 'pending'
                             CHECK(status IN ('pending','confirmed','shipped','completed','cancelled')),
                full_name    TEXT,
                phone        TEXT,
                province     TEXT,
                city         TEXT,
                address      TEXT,
                postal_code  TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        await db.commit()
