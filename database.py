import sqlite3
import os
from datetime import datetime, timedelta, date

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        is_premium INTEGER DEFAULT 0,
        premium_expires_at TIMESTAMP,
        daily_generations INTEGER DEFAULT 0,
        last_active_date TEXT,
        warned_expiry INTEGER DEFAULT 0,
        platform_mode TEXT DEFAULT 'bb'
    )
    """)
    conn.commit()

    # Safely migrate existing databases if platform_mode column does not exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN platform_mode TEXT DEFAULT 'bb'")
        conn.commit()
    except Exception:
        pass

    conn.close()

def get_or_create_user(user_id: int, username: str = None, first_name: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    today_str = str(date.today())

    if not row:
        cursor.execute("""
        INSERT INTO users (user_id, username, first_name, is_premium, daily_generations, last_active_date, warned_expiry, platform_mode)
        VALUES (?, ?, ?, 0, 0, ?, 0, 'bb')
        """, (user_id, username, first_name, today_str))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
    else:
        # Check if new day, reset daily count
        if row["last_active_date"] != today_str:
            cursor.execute("""
            UPDATE users SET daily_generations = 0, last_active_date = ?, username = ?, first_name = ?
            WHERE user_id = ?
            """, (today_str, username, first_name, user_id))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

    # Check premium expiration
    if row["is_premium"] and row["premium_expires_at"]:
        try:
            exp = datetime.fromisoformat(row["premium_expires_at"])
            if datetime.now() > exp:
                cursor.execute("""
                UPDATE users SET is_premium = 0, premium_expires_at = NULL, warned_expiry = 0
                WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
        except Exception:
            pass

    conn.close()
    return dict(row)

def set_user_platform(user_id: int, mode: str):
    """Sets user platform mode: 'bb' (Bots.Business) or 'tbc' (TelebotCreator)"""
    mode = mode.lower()
    if mode not in ['bb', 'tbc']:
        mode = 'bb'
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET platform_mode = ? WHERE user_id = ?", (mode, user_id))
    if cursor.rowcount == 0:
        cursor.execute("""
        INSERT INTO users (user_id, platform_mode, daily_generations, last_active_date, warned_expiry)
        VALUES (?, ?, 0, ?, 0)
        """, (user_id, mode, str(date.today())))
    conn.commit()
    conn.close()

def get_user_platform(user_id: int) -> str:
    user = get_or_create_user(user_id)
    return user.get("platform_mode", "bb") or "bb"

def check_daily_limit(user_id: int) -> tuple[bool, int, int, bool]:
    """Returns (can_generate, used_today, total_limit, is_premium)"""
    user = get_or_create_user(user_id)
    is_premium = bool(user["is_premium"])
    limit = 15 if is_premium else 3
    used = user["daily_generations"]
    can_generate = used < limit
    return (can_generate, used, limit, is_premium)

def increment_daily_count(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET daily_generations = daily_generations + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_premium(user_id: int, days: int = 7) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    exp_time = datetime.now() + timedelta(days=days)
    exp_str = exp_time.isoformat()
    cursor.execute("""
    UPDATE users SET is_premium = 1, premium_expires_at = ?, warned_expiry = 0
    WHERE user_id = ?
    """, (exp_str, user_id))
    if cursor.rowcount == 0:
        cursor.execute("""
        INSERT INTO users (user_id, is_premium, premium_expires_at, daily_generations, last_active_date, warned_expiry)
        VALUES (?, 1, ?, 0, ?, 0)
        """, (user_id, exp_str, str(date.today())))
    conn.commit()
    conn.close()
    return exp_str

def remove_premium(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET is_premium = 0, premium_expires_at = NULL, warned_expiry = 0
    WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def get_expiring_premium_users() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    two_days_later = now + timedelta(days=2)
    cursor.execute("""
    SELECT * FROM users 
    WHERE is_premium = 1 
      AND premium_expires_at IS NOT NULL 
      AND warned_expiry = 0
    """)
    rows = cursor.fetchall()
    expiring = []
    for r in rows:
        try:
            exp = datetime.fromisoformat(r["premium_expires_at"])
            if now < exp <= two_days_later:
                expiring.append(dict(r))
        except Exception:
            pass
    conn.close()
    return expiring

def mark_expiry_warned(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET warned_expiry = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as prem FROM users WHERE is_premium = 1")
    prem = cursor.fetchone()["prem"]
    conn.close()
    return {"total_users": total, "premium_users": prem}

# Initialize table on import
init_db()
