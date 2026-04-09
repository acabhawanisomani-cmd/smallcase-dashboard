"""SQLite database layer for Smallcase Dashboard."""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smallcase_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

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
    cur.execute(
        "INSERT INTO smallcases (name, description, total_investable_amount, is_design_mode) "
        "VALUES (?, ?, ?, ?)",
        (name, description, total_amount, int(is_design))
    )
    sc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sc_id


def get_all_smallcases() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM smallcases ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_smallcase(sc_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM smallcases WHERE id = ?", (sc_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_smallcase(sc_id: int, **kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [sc_id]
    conn.cursor().execute(
        f"UPDATE smallcases SET {sets}, updated_at = datetime('now','localtime') WHERE id = ?", vals
    )
    conn.commit()
    conn.close()


def delete_smallcase(sc_id: int):
    conn = get_connection()
    conn.cursor().execute("DELETE FROM smallcases WHERE id = ?", (sc_id,))
    conn.commit()
    conn.close()


def deploy_smallcase(sc_id: int):
    """Convert a design-mode smallcase to live."""
    conn = get_connection()
    conn.cursor().execute(
        "UPDATE smallcases SET is_design_mode = 0, updated_at = datetime('now','localtime') WHERE id = ?",
        (sc_id,)
    )
    conn.commit()
    conn.close()


# ── Holdings CRUD ───────────────────────────────────────────────────────────

def add_holding(smallcase_id: int, ticker: str, scrip_name: str, industry: str,
                weightage: float, buy_price: float, buy_date: str, units: float) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO holdings (smallcase_id, ticker, scrip_name, industry, weightage,
                              buy_price, buy_date, units)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (smallcase_id, ticker, scrip_name, industry, weightage, buy_price, buy_date, units))
    h_id = cur.lastrowid

    # Record BUY transaction
    if buy_price > 0 and units > 0:
        cur.execute("""
            INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date)
            VALUES (?, ?, ?, 'BUY', ?, ?, ?)
        """, (h_id, smallcase_id, ticker, units, buy_price, buy_date))

    conn.commit()
    conn.close()
    return h_id


def get_holdings(smallcase_id: int, active_only: bool = True) -> pd.DataFrame:
    conn = get_connection()
    query = "SELECT * FROM holdings WHERE smallcase_id = ?"
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY weightage DESC"
    df = pd.read_sql_query(query, conn, params=(smallcase_id,))
    conn.close()
    return df


def update_holding(holding_id: int, **kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [holding_id]
    conn.cursor().execute(
        f"UPDATE holdings SET {sets}, updated_at = datetime('now','localtime') WHERE id = ?", vals
    )
    conn.commit()
    conn.close()


def delete_holding(holding_id: int):
    conn = get_connection()
    conn.cursor().execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
    conn.commit()
    conn.close()


def exit_holding(holding_id: int, exit_price: float, exit_date: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker, smallcase_id, units FROM holdings WHERE id = ?", (holding_id,))
    row = cur.fetchone()
    if row:
        ticker, sc_id, units = row["ticker"], row["smallcase_id"], row["units"]
        cur.execute("""
            UPDATE holdings SET exit_price = ?, exit_date = ?, is_active = 0,
                                updated_at = datetime('now','localtime') WHERE id = ?
        """, (exit_price, exit_date, holding_id))
        cur.execute("""
            INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date)
            VALUES (?, ?, ?, 'SELL', ?, ?, ?)
        """, (holding_id, sc_id, ticker, units, exit_price, exit_date))
    conn.commit()
    conn.close()


# ── Residual (LIQUIDCASE) Rebalancing ──────────────────────────────────────

RESIDUAL_TICKER = "LIQUIDCASE"


def get_residual_holding(smallcase_id: int) -> dict | None:
    """Get the LIQUIDCASE (residual/sweep) holding for a smallcase."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM holdings WHERE smallcase_id = ? AND ticker = ? AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def rebalance_residual(smallcase_id: int, total_amount: float,
                       exit_price: float | None = None) -> dict | None:
    """
    Auto-adjust LIQUIDCASE to absorb remaining allocation.
    Returns a summary dict of what changed, or None if no LIQUIDCASE exists.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Find the residual holding
    cur.execute(
        "SELECT * FROM holdings WHERE smallcase_id = ? AND ticker = ? AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    residual = dict(row)

    # Sum all OTHER active holdings' weightages
    cur.execute(
        "SELECT COALESCE(SUM(weightage), 0) as total FROM holdings "
        "WHERE smallcase_id = ? AND ticker != ? AND is_active = 1",
        (smallcase_id, RESIDUAL_TICKER),
    )
    other_wt_sum = cur.fetchone()["total"]

    old_wt = residual["weightage"]
    old_units = residual["units"]
    buy_price = residual["buy_price"]

    new_wt = max(0.0, round(100.0 - other_wt_sum, 2))
    new_units = round((new_wt / 100 * total_amount) / buy_price, 4) if buy_price > 0 else 0

    delta_units = round(new_units - old_units, 4)

    # Update the residual holding
    cur.execute(
        "UPDATE holdings SET weightage = ?, units = ?, updated_at = datetime('now','localtime') WHERE id = ?",
        (new_wt, new_units, residual["id"]),
    )

    # Log transaction if units changed
    today = datetime.now().strftime("%Y-%m-%d")
    if delta_units < 0:
        sell_price = exit_price if exit_price and exit_price > 0 else buy_price
        cur.execute(
            "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
            "VALUES (?, ?, ?, 'SELL', ?, ?, ?)",
            (residual["id"], smallcase_id, RESIDUAL_TICKER, abs(delta_units), sell_price, today),
        )
    elif delta_units > 0:
        cur.execute(
            "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
            "VALUES (?, ?, ?, 'BUY', ?, ?, ?)",
            (residual["id"], smallcase_id, RESIDUAL_TICKER, delta_units, buy_price, today),
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
        "SELECT * FROM transactions WHERE smallcase_id = ? ORDER BY transaction_date DESC",
        conn, params=(smallcase_id,)
    )
    conn.close()
    return df


init_db()
