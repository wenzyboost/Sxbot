import sqlite3
from datetime import date, datetime


def get_conn():
    conn = sqlite3.connect("brixhub.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            searches_today INTEGER DEFAULT 0,
            last_search_date TEXT,
            is_premium INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    conn.close()
    return row


def reset_if_new_day(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    today = str(date.today())
    user = get_user(user_id)
    if user is None:
        c.execute(
            "INSERT INTO users (user_id, searches_today, last_search_date) VALUES (?, 0, ?)",
            (str(user_id), today),
        )
        conn.commit()
    elif user["last_search_date"] != today:
        c.execute(
            "UPDATE users SET searches_today = 0, last_search_date = ? WHERE user_id = ?",
            (today, str(user_id)),
        )
        conn.commit()
    conn.close()


def increment_search(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET searches_today = searches_today + 1 WHERE user_id = ?",
        (str(user_id),),
    )
    conn.commit()
    conn.close()


def can_search(user_id: str, limit: int) -> bool:
    reset_if_new_day(user_id)
    user = get_user(user_id)
    if user["is_premium"] == 1:
        return True
    return user["searches_today"] < limit


def set_premium(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()


def open_ticket(user_id: str, username: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tickets (user_id, username, status, created_at) VALUES (?, ?, 'open', ?)",
        (str(user_id), username, str(datetime.utcnow())),
    )
    conn.commit()
    ticket_id = c.lastrowid
    conn.close()
    return ticket_id


def get_all_tickets():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def close_ticket(ticket_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM users")
    total_users = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) as total FROM users WHERE is_premium = 1")
    premium_users = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) as total FROM tickets WHERE status = 'open'")
    open_tickets = c.fetchone()["total"]
    conn.close()
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "open_tickets": open_tickets,
    }
