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
        # Use the connection string exactly as provided in Streamlit secrets.
        # Enable "Connection pooling" in Neon's Connect dialog and paste that
        # pooled URL directly into DATABASE_URL. We deliberately do NOT rewrite
        # the host here — the old rewrite could produce an invalid hostname
        # (e.g. ...aws-pooler.neon.tech) that hangs until the connect timeout.
        db_url = _DATABASE_URL

        # Short connect timeout + a few quick retries. Neon free-tier databases
        # auto-suspend and take a few seconds to wake; we retry to give them time,
        # but never hang so long that Streamlit Cloud kills the app on startup
        # (a 120s hang exceeds the platform health-check window → "Oh no" crash).
        last_err = None
        for attempt in range(4):
            try:
                conn = psycopg2.connect(db_url, connect_timeout=15,
                                        keepalives=1, keepalives_idle=30,
                                        keepalives_interval=10, keepalives_count=5)
                conn.autocommit = False
                return conn
            except Exception as e:
                last_err = e
                if attempt < 3:
                    time.sleep(2 * (attempt + 1))  # 2s, 4s, 6s
                else:
                    raise last_err
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
                group_name TEXT DEFAULT '',
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
                stop_loss DOUBLE PRECISION DEFAULT 0,
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
                group_name TEXT DEFAULT '',
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
                stop_loss REAL DEFAULT 0,
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

    # ── Mutual Funds table ──────────────────────────────────────────────────
    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mutual_funds (
                id SERIAL PRIMARY KEY,
                scheme_code INTEGER,
                fund_name TEXT NOT NULL,
                amc TEXT DEFAULT '',
                category TEXT DEFAULT '',
                units DOUBLE PRECISION DEFAULT 0,
                avg_nav DOUBLE PRECISION DEFAULT 0,
                purchase_date TEXT,
                folio_number TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mutual_funds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_code INTEGER,
                fund_name TEXT NOT NULL,
                amc TEXT DEFAULT '',
                category TEXT DEFAULT '',
                units REAL DEFAULT 0,
                avg_nav REAL DEFAULT 0,
                purchase_date TEXT,
                folio_number TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

    # ── Advisory clients ────────────────────────────────────────────────────
    # A client has a mandate (capital we're authorised to deploy) and their own
    # holdings, so undeployed cash is meaningful — unlike a folio, which is
    # weight-based.
    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT DEFAULT '',
                mandate_amount DOUBLE PRECISION DEFAULT 0,
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_holdings (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                scrip_name TEXT NOT NULL,
                units DOUBLE PRECISION DEFAULT 0,
                buy_price DOUBLE PRECISION DEFAULT 0,
                buy_date TEXT,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT DEFAULT '',
                mandate_amount REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                scrip_name TEXT NOT NULL,
                units REAL DEFAULT 0,
                buy_price REAL DEFAULT 0,
                buy_date TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

    # ── Realized gains ledger (per client) ──────────────────────────────────
    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_realized (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                ticker TEXT DEFAULT '',
                scrip_name TEXT NOT NULL,
                units DOUBLE PRECISION DEFAULT 0,
                buy_price DOUBLE PRECISION DEFAULT 0,
                sell_price DOUBLE PRECISION DEFAULT 0,
                buy_date TEXT,
                sell_date TEXT,
                charges DOUBLE PRECISION DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_realized (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                ticker TEXT DEFAULT '',
                scrip_name TEXT NOT NULL,
                units REAL DEFAULT 0,
                buy_price REAL DEFAULT 0,
                sell_price REAL DEFAULT 0,
                buy_date TEXT,
                sell_date TEXT,
                charges REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

    # ── Work tracker ────────────────────────────────────────────────────────
    # Recurring tasks. Completion is recorded per period (a daily task done
    # today is still pending tomorrow), so work_log holds one row per
    # task+period rather than a single done flag on the task.
    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                frequency TEXT NOT NULL DEFAULT 'daily',
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_log (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL REFERENCES work_tasks(id) ON DELETE CASCADE,
                period_key TEXT NOT NULL,
                done_at TIMESTAMP DEFAULT NOW(),
                notes TEXT DEFAULT '',
                UNIQUE (task_id, period_key)
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                frequency TEXT NOT NULL DEFAULT 'daily',
                notes TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL REFERENCES work_tasks(id) ON DELETE CASCADE,
                period_key TEXT NOT NULL,
                done_at TEXT DEFAULT (datetime('now','localtime')),
                notes TEXT DEFAULT '',
                UNIQUE (task_id, period_key)
            )
        """)

    # ── Scrip → NSE ticker memory ───────────────────────────────────────────
    # Broker statements carry scrip names but no tickers. Remember every
    # mapping the user confirms so repeat uploads need no re-typing.
    if _USE_PG:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scrip_ticker_map (
                scrip_key TEXT PRIMARY KEY,
                scrip_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scrip_ticker_map (
                scrip_key TEXT PRIMARY KEY,
                scrip_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

    # ── Migrations: add columns that didn't exist in older schema ──
    try:
        if _USE_PG:
            cur.execute("ALTER TABLE holdings ADD COLUMN IF NOT EXISTS stop_loss DOUBLE PRECISION DEFAULT 0")
            cur.execute("ALTER TABLE smallcases ADD COLUMN IF NOT EXISTS group_name TEXT DEFAULT ''")
        else:
            cur.execute("PRAGMA table_info(holdings)")
            h_cols = [r[1] for r in cur.fetchall()]
            if "stop_loss" not in h_cols:
                cur.execute("ALTER TABLE holdings ADD COLUMN stop_loss REAL DEFAULT 0")
            cur.execute("PRAGMA table_info(smallcases)")
            s_cols = [r[1] for r in cur.fetchall()]
            if "group_name" not in s_cols:
                cur.execute("ALTER TABLE smallcases ADD COLUMN group_name TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists — ignore

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
                weightage: float, buy_price: float, buy_date: str, units: float,
                stop_loss: float = 0.0) -> int:
    conn = get_connection()
    cur = conn.cursor()

    if _USE_PG:
        cur.execute(f"""
            INSERT INTO holdings (smallcase_id, ticker, scrip_name, industry, weightage,
                                  buy_price, buy_date, units, stop_loss)
            VALUES ({_ph(9)}) RETURNING id
        """, (smallcase_id, ticker, scrip_name, industry, weightage, buy_price, buy_date, units, stop_loss))
    else:
        cur.execute(f"""
            INSERT INTO holdings (smallcase_id, ticker, scrip_name, industry, weightage,
                                  buy_price, buy_date, units, stop_loss)
            VALUES ({_ph(9)})
        """, (smallcase_id, ticker, scrip_name, industry, weightage, buy_price, buy_date, units, stop_loss))

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


def delete_all_active_holdings(smallcase_id: int):
    """Remove all active holdings for a folio — used by R Wadiwala statement import."""
    conn = get_connection()
    conn.cursor().execute(
        f"DELETE FROM holdings WHERE smallcase_id = {_ph()} AND is_active = 1",
        (smallcase_id,)
    )
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


# ── Realized P/L (from exited holdings) ────────────────────────────────────

def get_realized_pnl(smallcase_id: int) -> dict:
    """Return realized P/L stats for all exited holdings in a smallcase.

    Realized P/L = SUM((exit_price - buy_price) * units) for is_active=0 holdings.
    Excludes LIQUIDCASE sweep movements (they are rebalancing, not trading P/L).
    """
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()
    cur.execute(
        f"""
        SELECT ticker, scrip_name, buy_price, exit_price, units, buy_date, exit_date
        FROM holdings
        WHERE smallcase_id = {ph}
          AND is_active = 0
          AND ticker != {ph}
          AND exit_price IS NOT NULL
        """,
        (smallcase_id, RESIDUAL_TICKER),
    )
    rows = _fetchall_dict(cur)
    conn.close()

    total_realized = 0.0
    total_cost = 0.0
    total_proceeds = 0.0
    details = []
    for r in rows:
        bp = float(r["buy_price"] or 0)
        ep = float(r["exit_price"] or 0)
        u = float(r["units"] or 0)
        if u <= 0 or bp <= 0 or ep <= 0:
            continue
        cost = bp * u
        proceeds = ep * u
        pnl = proceeds - cost
        total_cost += cost
        total_proceeds += proceeds
        total_realized += pnl
        details.append({
            "ticker": r["ticker"],
            "scrip_name": r["scrip_name"],
            "units": u,
            "buy_price": bp,
            "exit_price": ep,
            "buy_date": r["buy_date"],
            "exit_date": r["exit_date"],
            "cost": cost,
            "proceeds": proceeds,
            "pnl": pnl,
            "pnl_pct": (pnl / cost * 100) if cost > 0 else 0,
        })

    return {
        "total_realized": round(total_realized, 2),
        "total_cost": round(total_cost, 2),
        "total_proceeds": round(total_proceeds, 2),
        "details": details,
    }


# ── Closed Position Edit / Reopen ──────────────────────────────────────────

def update_closed_position(holding_id: int, exit_price: float, exit_date: str):
    """Update the exit_price/exit_date of a closed (is_active=0) holding,
    AND update its corresponding SELL transaction to match."""
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()

    # Update the holding
    cur.execute(
        f"UPDATE holdings SET exit_price = {ph}, exit_date = {ph}, "
        f"updated_at = {_now_expr()} WHERE id = {ph}",
        (exit_price, exit_date, holding_id),
    )

    # Update the most recent SELL transaction for this holding
    cur.execute(
        f"SELECT id FROM transactions WHERE holding_id = {ph} AND action = 'SELL' "
        f"ORDER BY id DESC LIMIT 1",
        (holding_id,),
    )
    row = cur.fetchone()
    if row:
        txn_id = row[0]
        cur.execute(
            f"UPDATE transactions SET price = {ph}, transaction_date = {ph} WHERE id = {ph}",
            (exit_price, exit_date, txn_id),
        )

    conn.commit()
    conn.close()


def reopen_closed_position(holding_id: int):
    """Mark a closed holding as active again (clears exit_price/exit_date).
    Also deletes the associated SELL transaction."""
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()

    # Delete the SELL transaction(s) for this holding
    cur.execute(
        f"DELETE FROM transactions WHERE holding_id = {ph} AND action = 'SELL'",
        (holding_id,),
    )

    # Reactivate the holding
    if _USE_PG:
        cur.execute(
            f"UPDATE holdings SET is_active = 1, exit_price = 0, exit_date = NULL, "
            f"updated_at = {_now_expr()} WHERE id = {ph}",
            (holding_id,),
        )
    else:
        cur.execute(
            f"UPDATE holdings SET is_active = 1, exit_price = 0, exit_date = NULL, "
            f"updated_at = {_now_expr()} WHERE id = {ph}",
            (holding_id,),
        )

    conn.commit()
    conn.close()


# ── Transactions ────────────────────────────────────────────────────────────

def delete_transaction(transaction_id: int):
    """Delete a single transaction by ID. Holdings table is NOT auto-adjusted —
    use this only for stray/bogus transactions."""
    conn = get_connection()
    conn.cursor().execute(
        f"DELETE FROM transactions WHERE id = {_ph()}", (transaction_id,)
    )
    conn.commit()
    conn.close()


def update_transaction(transaction_id: int, **kwargs):
    """Update fields of a transaction (price, units, transaction_date, action)."""
    if not kwargs:
        return
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [transaction_id]
    conn.cursor().execute(
        f"UPDATE transactions SET {sets} WHERE id = {ph}", vals
    )
    conn.commit()
    conn.close()


def get_transactions(smallcase_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM transactions WHERE smallcase_id = {_ph()} ORDER BY transaction_date DESC",
        conn, params=(smallcase_id,)
    )
    conn.close()
    return df


def log_transaction(holding_id: int, smallcase_id: int, ticker: str,
                    action: str, units: float, price: float, txn_date: str):
    """Insert a single transaction row using the correct placeholder for the active DB backend."""
    conn = get_connection()
    conn.cursor().execute(
        f"INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
        f"VALUES ({_ph(7)})",
        (holding_id, smallcase_id, ticker, action, units, price, txn_date)
    )
    conn.commit()
    conn.close()


# ── Mutual Fund CRUD ────────────────────────────────────────────────────────

def get_all_mutual_funds() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mutual_funds ORDER BY created_at DESC")
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


def add_mutual_fund(scheme_code: int, fund_name: str, amc: str, category: str,
                    units: float, avg_nav: float, purchase_date: str,
                    folio_number: str = "", notes: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    if _USE_PG:
        cur.execute(
            "INSERT INTO mutual_funds (scheme_code, fund_name, amc, category, units, avg_nav, "
            "purchase_date, folio_number, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (scheme_code, fund_name, amc, category, units, avg_nav, purchase_date, folio_number, notes)
        )
    else:
        cur.execute(
            "INSERT INTO mutual_funds (scheme_code, fund_name, amc, category, units, avg_nav, "
            "purchase_date, folio_number, notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (scheme_code, fund_name, amc, category, units, avg_nav, purchase_date, folio_number, notes)
        )
    mf_id = _last_id(cur, "mutual_funds")
    conn.commit()
    conn.close()
    return mf_id


def update_mutual_fund(mf_id: int, **kwargs):
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [mf_id]
    conn.cursor().execute(f"UPDATE mutual_funds SET {sets} WHERE id = {ph}", vals)
    conn.commit()
    conn.close()


def delete_mutual_fund(mf_id: int):
    conn = get_connection()
    conn.cursor().execute(f"DELETE FROM mutual_funds WHERE id = {_ph()}", (mf_id,))
    conn.commit()
    conn.close()


# ── Advisory clients CRUD ───────────────────────────────────────────────────

def get_all_clients(active_only: bool = True) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    q = "SELECT * FROM clients"
    if active_only:
        q += " WHERE is_active = 1"
    q += " ORDER BY name"
    cur.execute(q)
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


def get_client(client_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM clients WHERE id = {_ph()}", (client_id,))
    row = _fetch_dict(cur)
    conn.close()
    return row


def add_client(name: str, mandate_amount: float = 0, code: str = "",
               notes: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cols = "(name, code, mandate_amount, notes)"
    if _USE_PG:
        cur.execute(f"INSERT INTO clients {cols} VALUES ({_ph(4)}) RETURNING id",
                    (name, code, mandate_amount, notes))
    else:
        cur.execute(f"INSERT INTO clients {cols} VALUES ({_ph(4)})",
                    (name, code, mandate_amount, notes))
    cid = _last_id(cur, "clients")
    conn.commit()
    conn.close()
    return cid


def update_client(client_id: int, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [client_id]
    conn.cursor().execute(
        f"UPDATE clients SET {sets}, updated_at = {_now_expr()} WHERE id = {ph}", vals
    )
    conn.commit()
    conn.close()


def delete_client(client_id: int):
    """Deletes the client and (via cascade) all their holdings."""
    conn = get_connection()
    cur = conn.cursor()
    # SQLite needs the child rows removed explicitly unless FKs are enforced
    cur.execute(f"DELETE FROM client_holdings WHERE client_id = {_ph()}", (client_id,))
    cur.execute(f"DELETE FROM clients WHERE id = {_ph()}", (client_id,))
    conn.commit()
    conn.close()


def get_client_holdings(client_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM client_holdings WHERE client_id = {_ph()} ORDER BY scrip_name",
        conn, params=(client_id,),
    )
    conn.close()
    return df


def add_client_holding(client_id: int, ticker: str, scrip_name: str,
                       units: float, buy_price: float, buy_date: str = "",
                       notes: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cols = "(client_id, ticker, scrip_name, units, buy_price, buy_date, notes)"
    args = (client_id, ticker, scrip_name, units, buy_price, buy_date, notes)
    if _USE_PG:
        cur.execute(f"INSERT INTO client_holdings {cols} VALUES ({_ph(7)}) RETURNING id", args)
    else:
        cur.execute(f"INSERT INTO client_holdings {cols} VALUES ({_ph(7)})", args)
    hid = _last_id(cur, "client_holdings")
    conn.commit()
    conn.close()
    return hid


def update_client_holding(holding_id: int, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    vals = list(kwargs.values()) + [holding_id]
    conn.cursor().execute(
        f"UPDATE client_holdings SET {sets}, updated_at = {_now_expr()} WHERE id = {ph}", vals
    )
    conn.commit()
    conn.close()


def delete_client_holding(holding_id: int):
    conn = get_connection()
    conn.cursor().execute(f"DELETE FROM client_holdings WHERE id = {_ph()}", (holding_id,))
    conn.commit()
    conn.close()


def get_client_realized(client_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        f"SELECT * FROM client_realized WHERE client_id = {_ph()} "
        f"ORDER BY sell_date DESC, id DESC",
        conn, params=(client_id,),
    )
    conn.close()
    return df


def add_client_realized(client_id: int, scrip_name: str, units: float,
                        buy_price: float, sell_price: float,
                        buy_date: str = "", sell_date: str = "",
                        ticker: str = "", charges: float = 0.0,
                        notes: str = "") -> int:
    conn = get_connection()
    cur = conn.cursor()
    cols = ("(client_id, ticker, scrip_name, units, buy_price, sell_price, "
            "buy_date, sell_date, charges, notes)")
    args = (client_id, ticker, scrip_name, units, buy_price, sell_price,
            buy_date, sell_date, charges, notes)
    if _USE_PG:
        cur.execute(f"INSERT INTO client_realized {cols} VALUES ({_ph(10)}) RETURNING id", args)
    else:
        cur.execute(f"INSERT INTO client_realized {cols} VALUES ({_ph(10)})", args)
    rid = _last_id(cur, "client_realized")
    conn.commit()
    conn.close()
    return rid


def delete_client_realized(realized_id: int):
    conn = get_connection()
    conn.cursor().execute(
        f"DELETE FROM client_realized WHERE id = {_ph()}", (realized_id,))
    conn.commit()
    conn.close()


def book_client_sale(client_id: int, holding_id: int, units_sold: float,
                     sell_price: float, sell_date: str, charges: float = 0.0,
                     notes: str = "") -> int:
    """Record a sale against an existing holding and reduce (or remove) it.

    Done in one transaction so the ledger entry and the position change can
    never diverge.
    """
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()
    try:
        cur.execute(f"SELECT * FROM client_holdings WHERE id = {ph}", (holding_id,))
        row = _fetch_dict(cur)
        if not row:
            raise ValueError("Holding not found.")
        held = float(row["units"] or 0)
        if units_sold <= 0:
            raise ValueError("Units sold must be greater than zero.")
        if units_sold > held + 1e-9:
            raise ValueError(f"Cannot sell {units_sold:g} — only {held:g} held.")

        cur.execute(
            f"INSERT INTO client_realized (client_id, ticker, scrip_name, units, "
            f"buy_price, sell_price, buy_date, sell_date, charges, notes) "
            f"VALUES ({_ph(10)})",
            (client_id, row["ticker"], row["scrip_name"], units_sold,
             float(row["buy_price"] or 0), sell_price, row["buy_date"] or "",
             sell_date, charges, notes))
        rid = _last_id(cur, "client_realized")

        remaining = round(held - units_sold, 6)
        if remaining <= 1e-9:
            cur.execute(f"DELETE FROM client_holdings WHERE id = {ph}", (holding_id,))
        else:
            cur.execute(
                f"UPDATE client_holdings SET units = {ph}, updated_at = {_now_expr()} "
                f"WHERE id = {ph}", (remaining, holding_id))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()
    return rid


# ── Work tracker CRUD ───────────────────────────────────────────────────────

WORK_FREQUENCIES = ("daily", "weekly", "monthly")


def get_work_tasks(active_only: bool = True) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    q = "SELECT * FROM work_tasks"
    if active_only:
        q += " WHERE is_active = 1"
    q += " ORDER BY frequency, id"
    cur.execute(q)
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


def add_work_task(title: str, frequency: str = "daily", notes: str = "") -> int:
    freq = frequency if frequency in WORK_FREQUENCIES else "daily"
    conn = get_connection()
    cur = conn.cursor()
    if _USE_PG:
        cur.execute("INSERT INTO work_tasks (title, frequency, notes) "
                    "VALUES (%s, %s, %s) RETURNING id", (title, freq, notes))
    else:
        cur.execute("INSERT INTO work_tasks (title, frequency, notes) "
                    "VALUES (?, ?, ?)", (title, freq, notes))
    tid = _last_id(cur, "work_tasks")
    conn.commit()
    conn.close()
    return tid


def update_work_task(task_id: int, **kwargs):
    if not kwargs:
        return
    conn = get_connection()
    ph = _ph()
    sets = ", ".join(f"{k} = {ph}" for k in kwargs)
    conn.cursor().execute(f"UPDATE work_tasks SET {sets} WHERE id = {ph}",
                          list(kwargs.values()) + [task_id])
    conn.commit()
    conn.close()


def delete_work_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM work_log WHERE task_id = {_ph()}", (task_id,))
    cur.execute(f"DELETE FROM work_tasks WHERE id = {_ph()}", (task_id,))
    conn.commit()
    conn.close()


def mark_work_done(task_id: int, period_key: str, notes: str = ""):
    """Idempotent — marking an already-completed period is a no-op."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if _USE_PG:
            cur.execute(
                "INSERT INTO work_log (task_id, period_key, notes) VALUES (%s, %s, %s) "
                "ON CONFLICT (task_id, period_key) DO NOTHING",
                (task_id, period_key, notes))
        else:
            cur.execute(
                "INSERT OR IGNORE INTO work_log (task_id, period_key, notes) "
                "VALUES (?, ?, ?)", (task_id, period_key, notes))
        conn.commit()
    finally:
        conn.close()


def unmark_work_done(task_id: int, period_key: str):
    conn = get_connection()
    ph = _ph()
    conn.cursor().execute(
        f"DELETE FROM work_log WHERE task_id = {ph} AND period_key = {ph}",
        (task_id, period_key))
    conn.commit()
    conn.close()


def get_done_periods(period_keys: list[str]) -> set:
    """{(task_id, period_key)} already completed, for the given periods."""
    if not period_keys:
        return set()
    conn = get_connection()
    cur = conn.cursor()
    marks = ", ".join([_ph()] * len(period_keys))
    cur.execute(f"SELECT task_id, period_key FROM work_log "
                f"WHERE period_key IN ({marks})", tuple(period_keys))
    rows = cur.fetchall()
    conn.close()
    out = set()
    for r in rows:
        out.add((r[0], r[1]) if isinstance(r, tuple) else (r["task_id"], r["period_key"]))
    return out


def get_last_done(task_id: int) -> str | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT period_key FROM work_log WHERE task_id = {_ph()} "
                f"ORDER BY period_key DESC LIMIT 1", (task_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return row[0] if isinstance(row, tuple) else row["period_key"]


def get_work_history(limit: int = 200) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT l.id, l.task_id, l.period_key, l.done_at, l.notes, "
        "t.title, t.frequency FROM work_log l "
        "JOIN work_tasks t ON t.id = l.task_id "
        "ORDER BY l.done_at DESC LIMIT " + str(int(limit)))
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


def scrip_key(name: str) -> str:
    """Normalise a scrip name so 'RAYMOND REALTY LTD.' and 'Raymond Realty'
    resolve to the same key."""
    import re as _re
    n = _re.sub(r"[^A-Za-z0-9 ]", " ", str(name or "")).upper()
    n = _re.sub(r"\b(LTD|LIMITED|LIMITE|THE|CO|COMPANY|PVT|PRIVATE|INDIA|"
                r"CORP|CORPORATION|EN|NET)\b", " ", n)
    return " ".join(n.split())


def get_ticker_map() -> dict[str, str]:
    """All remembered scrip_key -> ticker mappings."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT scrip_key, ticker FROM scrip_ticker_map")
        rows = cur.fetchall()
    except Exception:
        conn.close()
        return {}
    conn.close()
    if _USE_PG:
        return {r[0]: r[1] for r in rows}
    return {r["scrip_key"] if not isinstance(r, tuple) else r[0]:
            r["ticker"] if not isinstance(r, tuple) else r[1] for r in rows}


def save_ticker_mappings(pairs: dict[str, str]):
    """Upsert {scrip_name: ticker} pairs into the memory table."""
    if not pairs:
        return
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()
    for name, ticker in pairs.items():
        if not str(ticker).strip():
            continue
        key = scrip_key(name)
        if not key:
            continue
        tk = str(ticker).strip().upper()
        if _USE_PG:
            cur.execute(
                "INSERT INTO scrip_ticker_map (scrip_key, scrip_name, ticker) "
                "VALUES (%s, %s, %s) ON CONFLICT (scrip_key) DO UPDATE "
                "SET ticker = EXCLUDED.ticker, scrip_name = EXCLUDED.scrip_name, "
                "updated_at = NOW()",
                (key, str(name).strip(), tk))
        else:
            cur.execute(
                "INSERT INTO scrip_ticker_map (scrip_key, scrip_name, ticker) "
                "VALUES (?, ?, ?) ON CONFLICT(scrip_key) DO UPDATE "
                "SET ticker = excluded.ticker, scrip_name = excluded.scrip_name",
                (key, str(name).strip(), tk))
    conn.commit()
    conn.close()


def replace_client_holdings(client_id: int, rows: list[dict]):
    """Swap a client's holdings for `rows` in one transaction, so a failure
    can't leave the client with no positions.
    rows: [{ticker, scrip_name, units, buy_price, buy_date}]"""
    conn = get_connection()
    cur = conn.cursor()
    ph = _ph()
    try:
        cur.execute(f"DELETE FROM client_holdings WHERE client_id = {ph}", (client_id,))
        for r in rows:
            cur.execute(
                f"INSERT INTO client_holdings "
                f"(client_id, ticker, scrip_name, units, buy_price, buy_date) "
                f"VALUES ({_ph(6)})",
                (client_id, str(r["ticker"]).upper(), r["scrip_name"],
                 float(r["units"]), float(r["buy_price"]), r.get("buy_date", "")))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()


def search_holdings(query: str) -> list[dict]:
    """Search all active holdings by scrip_name or ticker across all smallcases.
    Returns list of dicts with holding + smallcase info."""
    conn = get_connection()
    ph = _ph()
    like = f"%{query.strip().upper()}%"
    cur = conn.cursor()
    cur.execute(f"""
        SELECT h.id, h.ticker, h.scrip_name, h.industry, h.weightage,
               h.buy_price, h.units, h.buy_date, h.stop_loss,
               s.id AS sc_id, s.name AS sc_name, s.group_name
        FROM holdings h
        JOIN smallcases s ON s.id = h.smallcase_id
        WHERE h.is_active = 1
          AND (UPPER(h.scrip_name) LIKE {ph} OR UPPER(h.ticker) LIKE {ph})
        ORDER BY s.group_name, s.name, h.scrip_name
    """, (like, like))
    rows = _fetchall_dict(cur)
    conn.close()
    return rows


# Run schema init at import time, but never let a database outage crash the
# whole app on import (that produces an unhelpful "Oh no" page). If the DB is
# unreachable, record the error so the UI can show it clearly instead.
INIT_ERROR: str | None = None
try:
    init_db()
except Exception as _e:
    INIT_ERROR = f"{type(_e).__name__}: {_e}"
