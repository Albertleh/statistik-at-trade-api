"""Database helper functions for Postgres connections and queries."""
import psycopg2
from psycopg2 import extras

from app.settings import settings


def get_conn():
    """Create a new database connection using environment-driven settings."""
    return psycopg2.connect(settings.database_dsn)


def fetch_one(sql: str, params: tuple):
    """Fetch a single row as a dict for a parameterized query."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def fetch_all(sql: str, params: tuple = ()):
    """Fetch all rows as a list of dicts for a parameterized query."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
