import asyncpg

pool = None

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(
        user='S1GMA',
        password='S1GMA',
        database='S1GMA',
        host='localhost')
    await pool.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT)""")
    await pool.execute("""
    CREATE TABLE IF NOT EXISTS themes(
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL UNIQUE)""")
    await pool.execute("""
    CREATE TABLE IF NOT EXISTS shops(
    id SERIAL PRIMARY KEY,
    theme_id INTEGER NOT NULL,
    title TEXT NOT NULL)""")
    await pool.execute("""
    ALTER TABLE shops
    ADD COLUMN IF NOT EXISTS photo TEXT,
    ADD COLUMN IF NOT EXISTS description TEXT;""")
    await pool.execute("""
    ALTER TABLE shops
    ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0""")
    await pool.execute("""
    CREATE TABLE IF NOT EXISTS shop_likes (
    user_id BIGINT NOT NULL,
    shop_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, shop_id))""")

async def update_username(user_id, username):
    await pool.execute(
        "UPDATE users SET username=$1 WHERE user_id=$2",
        username, user_id)
async def count_users():
    return await pool.fetchval("SELECT COUNT(*) FROM users")


async def add_theme(title: str):
    await pool.execute("INSERT INTO themes (title) VALUES ($1)", title)
async def delete_theme(title: str):
    await pool.execute("DELETE FROM themes WHERE title=$1", title)
async def get_themes():
    rows = await pool.fetch("SELECT title FROM themes ORDER BY title")
    return [r["title"] for r in rows]


async def add_shop(theme_id: int, title: str):
    await pool.execute(
        "INSERT INTO shops (theme_id, title) VALUES ($1, $2)",
        theme_id, title)
async def get_shops(theme_id: int):
    rows = await pool.fetch(
        "SELECT id, title FROM shops WHERE theme_id=$1 ORDER BY title",
        theme_id)
    return [{"id": r["id"], "title": r["title"]} for r in rows]
async def delete_shop(shop_id: int):
    await pool.execute("DELETE FROM shops WHERE id=$1", shop_id)
async def delete_shop_by_title(title: str):
    await pool.execute("DELETE FROM shops WHERE title=$1", title)
async def update_shop(shop_id: int, new_title: str):
    await pool.execute(
        "UPDATE shops SET title=$1 WHERE id=$2",
        new_title, shop_id)
    

async def update_shop_description(title: str, description: str, photo: str | None):
    await pool.execute(
        "UPDATE shops SET description=$1, photo=$2 WHERE title=$3",
        description, photo, title)
async def get_shop_by_title(title: str):
    return await pool.fetchrow(
        "SELECT * FROM shops WHERE title=$1", title)


async def has_liked(user_id, shop_id):
    row = await pool.fetchrow(
        "SELECT 1 FROM shop_likes WHERE user_id=$1 AND shop_id=$2",
        user_id, shop_id)
    return row is not None
async def add_like(user_id, shop_id):
    await pool.execute(
        "INSERT INTO shop_likes (user_id, shop_id) VALUES ($1, $2)",
        user_id, shop_id)
    await pool.execute(
        "UPDATE shops SET likes = likes + 1 WHERE id=$1",
        shop_id)
async def get_shop_likes(shop_id):
    return await pool.fetchval(
        "SELECT likes FROM shops WHERE id=$1",
        shop_id)
    
async def close_pool():
    await pool.close()