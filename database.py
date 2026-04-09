"""Database layer for Smallcase Dashboard — Neon PostgreSQL (primary) + SQLite (fallback)."""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# ── Connection Setup ───────────────────────────────────────────────────────
# Try PostgreSQL first (Neon), fallback to SQLite for offline use

_USE_PG = False
_DATABASE_URL = None

try:
    import streamlit as st
    if "DATABASE_URL" in st.secrets:
        _DATABASE_URL = st.secrets["DATABASE_URL"]
        import psycopg2
        import psycopg2.extras
        _USE_PG = True
except Exception:
    pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smallcase_data.db")


def get_connection():
    if _USE_PG:
        import time
        # Retry with backoff for Neon cold starts (scales to zero when idle)
        for attempt in range(3):
            try:
                conn = psycopg2.connect(_DATABASE_URL, connect_timeout=60,
                                        options="-c statement_timeout=30000")
                conn.autocommit = False
                return conn
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # 1s, 2s
                else:
                    raise e
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _ph(n=1):
    """Return n placeholder(s) — %s for PostgreSQL, ? for SQLite."""
    p = "%s" if _USE_PG else "?"
    return ", ".join([p] * n)


def _now_expr():
    """SQL expression for current timestamp."""
    return "NOW()" if _USE_PG else "datetime('now','localtime')"


def _fetch_dict(cursor):
    """Fetch one row as dict from cursor, works for both PG and SQLite."""
    row = cursor.fetchone()
    if row is None:
        return None
    if _USE_PG:
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    else:
        return dict(row)


def _fetchall_dict(cursor):
    """Fetch all rows as list of dicts."""
    rows = cursor.fetchall()
    if _USE_PG:
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, r)) for r in rows]
    else:
        return [dict(r) for r in rows]


def _last_id(cursor, table_name):
    """Get last inserted ID — PostgreSQL uses RETURNING, SQLite uses lastrowid."""
    if _USE_PG:
        row = cursor.fetchone()
        return row[0] if row else None
    else:
        return cursor.lastrowid


# ── Init ───────────────────────────────────────────────────────────────────

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS smallcases (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                total_investable_amount DOUBLE PRECISION DEFAULT 0,
                is_design_mode INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id SERIAL PRIMARY KEY,
                smallcase_id INTEGER NOT NULL REFERENCES smallcases(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                scrip_name TEXT NOT NULL,
                industry TEXT DEFAULT '',
                weightage DOUBLE PRECISION DEFAULT 0,
                buy_price DOUBLE PRECISION DEFAULT 0,
                buy_date TEXT,
                exit_date TEXT,
                exit_price DOUBLE PRECISION DEFAULT 0,
                units DOUBLE PRECISION DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                holding_id INTEGER NOT NULL REFERENCES holdings(id) ON DELETE CASCADE,
                smallcase_id INTEGER NOT NULL REFERENCES smallcases(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                units DOUBLE PRECISION NOT NULL,
                price DOUBLE PRECISION NOT NULL,
                transaction_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS smallcases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                total_investable_amount REAL DEFAULT 0,
                is_design_mode INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                smallcase_id INTEGER NOT NULL REFERENCES smallcases(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                scrip_name TEXT NOT NULL,
                industry TEXT DEFAULT '',
                weightage REAL DEFAULT 0,
                buy_price REAL DEFAULT 0,
                buy_date TEXT,
                exit_date TEXT,
                exit_price REAL DEFAULT 0,
                units REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holding_id INTEGER NOT NULL REFERENCES holdings(id) ON DELETE CASCADE,
                smallcase_id INTEGER NOT NULL REFERENCES smallcases(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                units REAL NOT NULL,
                price REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

    conn.commit()
    conn.close()


# ── Smallcase CRUD ──────────────────────────────────────────────────────────

def create_smallcase(name: str, description: str = "", total_amount: float = 0,
                     is_design: bool = False) -> int:
    conn = get_connection()
    cur = conn.cursor()
    if _USE_PG:
        cur.execute(
            "INSERT INTO smallcases (name, description, total_investable_amount, is_design_mode) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (name, description, total_amount, int(is_design))
        )
    else:
        cur.execute(
            "INSERT INTO smallcases (name, description, total_investable_amount, is_design_mode) "
            "VALUES (?, ?, ?, ?)",
            (name, description, total_amount, int(is_design))
        )
    sc_id = _last_id(cur, "smallcases")
    conn.commit()
    conn.close()
    return sc_id


def get_all_smallcases() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM smallcases ORDER BY created_at DESC")
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


def get_smallcase(sc_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM smallcases WHERE id = {_ph()}", (sc_id,))
    row = _fetch_dict(cur)
    conn.close()
    return row


def update_smallcase(sc_id: int, **kwargs):
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [sc_id]
    conn.cursor().execute(
        f"UPDATE smallcases SET {sets}, updated_at = {_now_expr()} WHERE id = {ph}", vals
    )
    conn.commit()
    conn.close()


def delete_smallcase(sc_id: int):
    conn = get_connection()
    conn.cursor().execute(f"DELETE FROM smallcases WHERE id = {_ph()}", (sc_id,))
    conn.commit()
    conn.close()


def deploy_smallcase(sc_id: int):
    """Convert a design-mode smallcase to live."""
    conn = get_connection()
    conn.cursor().execute(
        f"UPDATE smallcases SET is_design_mode = 0, updated_at = {_now_expr()} WHERE id = {_ph()}",
        (sc_id,)
    )
    conn.commit()
    conn.close()


# ── Holdings CRUD ───────────────────────────────────────────────────────────

def add_holding(smallcase_id: int, ticker: str, scrip_name: str, industry: str,
                weightage: float, buy_price: float, buy_date: str, units: float) -> int:
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()

    if _USE_PG:
        cur.execute(f"""
            INSERT INTO holdings (smallcase_id, ticker, scrip_name, industry, weightage,
                                  buy_price, buy_date, units)
            VALUES ({_ph(8)}) RETURNING id
        """, (smallcase_id, ticker, scrip_name, industry, weightage, buy_price, buy_date, units))
    else:
        cur.execute(f"""
            INSERT INTO holdings (smallcase_id, ticker, scrip_name, industry, weightage,
                                  buy_price, buy_date, units)
            VALUES ({_ph(8)})
        """, (smallcase_id, ticker, scrip_name, industry, weightage, buy_price, buy_date, units))

    h_id = _last_id(cur, "holdings")

    # Record BUY transaction
    if buy_price > 0 and units > 0:
        cur.execute(f"""
            INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date)
            VALUES ({_ph(7)})
        """, (h_id, smallcase_id, ticker, 'BUY', units, buy_price, buy_date))

    conn.commit()
    conn.close()
    return h_id


def get_holdings(smallcase_id: int, active_only: bool = True) -> pd.DataFrame:
    conn = get_connection()
    ph = _ph()
    query = f"SELECT * FROM holdings WHERE smallcase_id = {ph}"
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY weightage DESC"
    df = pd.read_sql_query(query, conn, params=(smallcase_id,))
    conn.close()
    return df


def update_holding(holding_id: int, **kwargs):
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [holding_id]
    conn.cursor().execute(
        f"UPDATE holdings SET {sets}, updated_at = {_now_expr()} WHERE id = {ph}", vals
    )
    conn.commit()
    conn.close()


def delete_holding(holding_id: int):
    conn = get_connection()
    conn.cursor().execute(f"DELETE FROM holdings WHERE id = {_ph()}", (holding_id,))
    conn.commit()
    conn.close()


def exit_holding(holding_id: int, exit_price: float, exit_date: str):
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()
    cur.execute(f"SELECT ticker, smallcase_id, units FROM holdings WHERE id = {ph}", (holding_id,))

    if _USE_PG:
        row = cur.fetchone()
        if row:
            ticker, sc_id, units = row[0], row[1], row[2]
    else:
        row = cur.fetchone()
        if row:
            ticker, sc_id, units = row["ticker"], row["smallcase_id"], row["units"]

    if row:
        cur.execute(f"""
            UPDATE holdings SET exit_price = {ph}, exit_date = {ph}, is_active = 0,
                                updated_at = {_now_expr()} WHERE id = {ph}
        """, (exit_price, exit_date, holding_id))
        cur.execute(f"""
            INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date)
            VALUES ({_ph(7)})
        """, (holding_id, sc_id, ticker, 'SELL', units, exit_price, exit_date))
    conn.commit()
    conn.close()


# ── Residual (LIQUIDCASE) Rebalancing ──────────────────────────────────────

RESIDUAL_TICKER = "LIQUIDCASE"


def get_residual_holding(smallcase_id: int) -> dict | None:
    """Get the LIQUIDCASE (residual/sweep) holding for a smallcase."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"SELECT * FROM holdings WHERE smallcase_id = {_ph()} AND ticker = {_ph()} AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    row = _fetch_dict(cur)
    conn.close()
    return row


def rebalance_residual(smallcase_id: int, total_amount: float,
                       exit_price: float | None = None) -> dict | None:
    """Auto-adjust LIQUIDCASE to absorb remaining allocation."""
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()

    # Find the residual holding
    cur.execute(
        f"SELECT * FROM holdings WHERE smallcase_id = {ph} AND ticker = {ph} AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    row = _fetch_dict(cur)
    if not row:
        conn.close()
        return None

    residual = row

    # Sum all OTHER active holdings' weightages
    cur.execute(
        f"SELECT COALESCE(SUM(weightage), 0) as total FROM holdings "
        f"WHERE smallcase_id = {ph} AND ticker != {ph} AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    if _USE_PG:
        other_wt_sum = cur.fetchone()[0]
    else:
        other_wt_sum = cur.fetchone()["total"]

    old_wt = residual["weightage"]
    old_units = residual["units"]
    buy_price = residual["buy_price"]

    new_wt = max(0.0, round(100.0 - other_wt_sum, 2))
    new_units = round((new_wt / 100 * total_amount) / buy_price, 4) if buy_price > 0 else 0

    delta_units = round(new_units - old_units, 4)

    # Update the residual holding
    cur.execute(
        f"UPDATE holdings SET weightage = {ph}, units = {ph}, updated_at = {_now_expr()} WHERE id = {ph}",
        (new_wt, new_units, residual["id"]),
    )

    # Log transaction if units changed
    today = datetime.now().strftime("%Y-%m-%d")
    if delta_units < 0:
        sell_price = exit_price if exit_price and exit_price > 0 else buy_price
        cur.execute(
            f"INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
            f"VALUES ({_ph(7)})",
            (residual["id"], smallcase_id, RESIDUAL_TICKER, 'SELL', abs(delta_units), sell_price, today),
        )
    elif delta_units > 0:
        cur.execute(
            f"INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
            f"VALUES ({_ph(7)})",
            (residual["id"], smallcase_id, RESIDUAL_TICKER, 'BUY', delta_units, buy_price, today),
        )

    conn.commit()
    conn.close()

    return {
        "old_wt": old_wt, "new_wt": new_wt,
        "old_units": old_units, "new_units": new_units,
        "delta_units": delta_units,
    }


# ── Transactions ────────────────────────────────────────────────────────────

def get_transactions(smallcase_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM transactions WHERE smallcase_id = {_ph()} ORDER BY transaction_date DESC",
        conn, params=(smallcase_id,)
    )
    conn.close()
    return df


init_db()
