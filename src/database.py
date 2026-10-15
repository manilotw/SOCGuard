
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "socguard.db"


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS auth_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                username TEXT,
                status TEXT NOT NULL,
                UNIQUE(timestamp, ip_address, username, status)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS brute_force_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                severity TEXT NOT NULL,
                UNIQUE(ip_address, start_time, end_time, severity)
            )
        """)


def save_events(events):
    saved = 0

    with get_connection() as connection:
        for event in events:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO auth_events
                (timestamp, ip_address, username, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.timestamp,
                    event.ip_address,
                    event.username,
                    event.status,
                ),
            )
            saved += cursor.rowcount

    return saved


def save_alerts(alerts):
    saved = 0

    with get_connection() as connection:
        for alert in alerts:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO brute_force_alerts
                (ip_address, attempts, start_time, end_time, severity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    alert.ip_address,
                    alert.attempts,
                    alert.start_time,
                    alert.end_time,
                    alert.severity,
                ),
            )
            saved += cursor.rowcount

    return saved


def get_recent_events(limit=5):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, ip_address, username, status
            FROM auth_events
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_recent_alerts(limit=10):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ip_address, attempts, start_time, end_time, severity
            FROM brute_force_alerts
            ORDER BY end_time DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DB_FILE}")
