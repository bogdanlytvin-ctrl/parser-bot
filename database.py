import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                first_name  TEXT,
                username    TEXT,
                lang        TEXT NOT NULL DEFAULT 'ua',
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                name         TEXT NOT NULL,
                source_type  TEXT NOT NULL,
                source_url   TEXT,
                keywords     TEXT,
                interval_min INTEGER NOT NULL DEFAULT 45,
                channel_id   TEXT NOT NULL,
                country      TEXT NOT NULL DEFAULT 'ua',
                niche        TEXT NOT NULL DEFAULT 'custom',
                ai_filter    INTEGER NOT NULL DEFAULT 0,
                is_active    INTEGER NOT NULL DEFAULT 1,
                last_run_at  TEXT,
                next_run_at  TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                url         TEXT NOT NULL,
                title       TEXT,
                description TEXT,
                price       TEXT,
                image_url   TEXT,
                pub_date    TEXT,
                hash        TEXT NOT NULL,
                sent_at     TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(task_id, hash)
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_next_run ON tasks(next_run_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_user     ON tasks(user_id);
            CREATE INDEX IF NOT EXISTS idx_results_task   ON results(task_id);
        """)

        # Migrations for existing DBs
        for col, ddl in [
            ("lang",      "ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'ua'"),
            ("country",   "ALTER TABLE tasks ADD COLUMN country TEXT NOT NULL DEFAULT 'ua'"),
            ("niche",     "ALTER TABLE tasks ADD COLUMN niche TEXT NOT NULL DEFAULT 'custom'"),
            ("ai_filter", "ALTER TABLE tasks ADD COLUMN ai_filter INTEGER NOT NULL DEFAULT 0"),
        ]:
            try:
                conn.execute(ddl)
            except Exception:
                pass


# -- Users ------------------------------------------------------------------

def upsert_user(telegram_id: int, first_name: str, username: str | None) -> int:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users (telegram_id, first_name, username)
            VALUES (?,?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                first_name = excluded.first_name,
                username   = excluded.username
        """, (telegram_id, first_name, username))
        return conn.execute(
            "SELECT id FROM users WHERE telegram_id=?", (telegram_id,)
        ).fetchone()["id"]


def get_user(telegram_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE telegram_id=?", (telegram_id,)
        ).fetchone()


def get_user_lang(telegram_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT lang FROM users WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
    return row["lang"] if row else "ua"


def set_user_lang(telegram_id: int, lang: str) -> None:
    if lang not in ("ua", "en"):
        lang = "ua"
    with get_conn() as conn:
        conn.execute("UPDATE users SET lang=? WHERE telegram_id=?", (lang, telegram_id))


# -- Tasks ------------------------------------------------------------------

def create_task(user_id: int, name: str, source_type: str,
                source_url: str, keywords: str, interval_min: int,
                channel_id: str, country: str = "ua",
                niche: str = "custom", ai_filter: bool = False) -> int:
    from datetime import timedelta
    next_run = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO tasks
                (user_id, name, source_type, source_url, keywords,
                 interval_min, channel_id, country, niche, ai_filter, next_run_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (user_id, name, source_type, source_url, keywords,
              interval_min, channel_id, country, niche, int(ai_filter), next_run))
        return cur.lastrowid


def get_user_tasks(user_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()


def get_task(task_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()


def toggle_task(task_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT is_active FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return False
        new_state = 0 if row["is_active"] else 1
        conn.execute("UPDATE tasks SET is_active=? WHERE id=?", (new_state, task_id))
        return bool(new_state)


def delete_task(task_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))


def update_task_schedule(task_id: int, last_run: str, next_run: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE tasks SET last_run_at=?, next_run_at=? WHERE id=?",
            (last_run, next_run, task_id)
        )


def get_due_tasks() -> list[sqlite3.Row]:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        return conn.execute("""
            SELECT * FROM tasks
            WHERE is_active=1
              AND (next_run_at IS NULL OR next_run_at <= ?)
        """, (now,)).fetchall()


# -- Results ----------------------------------------------------------------

def save_result(task_id: int, url: str, title: str, description: str,
                price: str, image_url: str, pub_date: str, hash_val: str) -> bool:
    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO results
                    (task_id, url, title, description, price, image_url, pub_date, hash)
                VALUES (?,?,?,?,?,?,?,?)
            """, (task_id, url, title, description, price, image_url, pub_date, hash_val))
            return True
        except sqlite3.IntegrityError:
            return False


def get_task_results(task_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM results WHERE task_id=? ORDER BY sent_at DESC LIMIT ?",
            (task_id, limit)
        ).fetchall()


def count_task_results(task_id: int) -> int:
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM results WHERE task_id=?", (task_id,)
        ).fetchone()[0]


# -- Admin stats ------------------------------------------------------------

def get_stats() -> dict:
    with get_conn() as conn:
        return {
            "total_users":   conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "total_tasks":   conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "active_tasks":  conn.execute("SELECT COUNT(*) FROM tasks WHERE is_active=1").fetchone()[0],
            "total_results": conn.execute("SELECT COUNT(*) FROM results").fetchone()[0],
            "results_today": conn.execute(
                "SELECT COUNT(*) FROM results WHERE date(sent_at)=date('now')"
            ).fetchone()[0],
        }
