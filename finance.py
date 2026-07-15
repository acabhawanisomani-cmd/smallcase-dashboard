"""Financial data fetching and calculations.

Prices come from Yahoo Finance's public chart JSON endpoint via plain `requests`.
We deliberately do NOT use the `yfinance` library: on Streamlit Cloud it pulls
native C-extensions (curl_cffi, frozendict, …) that segfault (signal 11) under
rate-limiting. Direct requests are pure-Python and simply fail gracefully.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import time
import requests
import streamlit as st

CACHE_TTL = 300  # 5 minutes

# Browser-like headers reduce Yahoo's bot throttling (what curl_cffi did natively)
_YHEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


def _ensure_ns_suffix(ticker: str) -> str:
    """Add .NS suffix for NSE tickers if not present."""
    t = ticker.strip().upper()
    if not t.endswith(".NS") and not t.endswith(".BO"):
        t += ".NS"
    return t


def _yahoo_chart(symbol: str, params: dict) -> dict | None:
    """Call Yahoo's chart endpoint and return result[0] dict, or None on failure.

    Pure requests — never raises, never segfaults. Tries both Yahoo hosts.
    """
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            resp = requests.get(
                f"https://{host}/v8/finance/chart/{symbol}",
                params=params, headers=_YHEADERS, timeout=10,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            result = (data.get("chart") or {}).get("result")
            if result:
                return result[0]
        except Exception:
            continue
    return None


def _empty_quote() -> dict:
    return {"current_price": 0, "prev_close": 0, "today_change": 0, "pct_change": 0}


def _yahoo_quote_direct(symbol: str) -> dict | None:
    """Current quote for a fully-qualified symbol (e.g. RELIANCE.NS)."""
    res = _yahoo_chart(symbol, {"range": "5d", "interval": "1d"})
    if not res:
        return None
    meta = res.get("meta") or {}

    # Daily closes over the window; None entries are non-trading gaps.
    closes: list[float] = []
    try:
        for c in res["indicators"]["quote"][0]["close"]:
            if c is not None:
                closes.append(float(c))
    except Exception:
        closes = []

    current = meta.get("regularMarketPrice")
    try:
        current = float(current) if current is not None else 0.0
    except (TypeError, ValueError):
        current = 0.0
    if current <= 0:
        current = closes[-1] if closes else 0.0
    if current <= 0:
        return None

    # Previous close = the PRIOR TRADING DAY's close, i.e. the second-to-last
    # entry of the daily series (the last entry is today's session).
    # Do NOT use meta["chartPreviousClose"]: with range=5d that is the close
    # from *before the whole window* (~a week back), which makes a 5-day move
    # show up as today's % change.
    prev = closes[-2] if len(closes) >= 2 else current

    change = current - prev
    pct = (change / prev * 100) if prev else 0.0
    return {
        "current_price": round(current, 2),
        "prev_close": round(prev, 2),
        "today_change": round(change, 2),
        "pct_change": round(pct, 2),
    }


def _quote_with_fallback(ticker: str) -> dict:
    """Try .NS first, then .BO (BSE) as fallback for SME / BSE-only stocks."""
    base = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
    for suffix in (".NS", ".BO"):
        q = _yahoo_quote_direct(base + suffix)
        if q:
            return q
    return _empty_quote()


# ── Live prices ─────────────────────────────────────────────────────────────

def fetch_live_data(tickers: list[str]) -> dict[str, dict]:
    """Fetch current price / prev close / change / % for a list of tickers."""
    return _fetch_live_data_cached(tuple(sorted(set(tickers))))


@st.cache_data(ttl=CACHE_TTL, show_spinner="Fetching live prices...")
def _fetch_live_data_cached(tickers: tuple) -> dict[str, dict]:
    """Cached live price fetch (per-symbol direct Yahoo calls, sequential)."""
    result = {}
    for t in tickers:
        try:
            result[t] = _quote_with_fallback(t)
        except Exception:
            result[t] = _empty_quote()
    return result


# ── Opening prices (for buy-date / execution-date pricing) ──────────────────

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_open_price(ticker: str, target_date: str) -> float | None:
    """Opening price on a date (or the next trading day). Tries NSE then BSE."""
    base = ticker.strip().upper().replace(".NS", "").replace(".BO", "")
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    except Exception:
        return None
    p1 = int(datetime(dt.year, dt.month, dt.day).timestamp())
    p2 = p1 + 8 * 86400
    for suffix in (".NS", ".BO"):
        res = _yahoo_chart(base + suffix,
                           {"period1": p1, "period2": p2, "interval": "1d"})
        if not res:
            continue
        try:
            opens = res["indicators"]["quote"][0]["open"]
            for o in opens:
                if o is not None and float(o) > 0:
                    return round(float(o), 2)
        except Exception:
            continue
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_open_prices_batch(tickers: list[str], target_date: str) -> dict[str, float | None]:
    """Opening prices for multiple tickers on a specific date."""
    return {t: fetch_open_price(t, target_date) for t in (tickers or [])}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_opening_price(ticker: str, date_str: str) -> float | None:
    """Alias kept for compatibility — opening price on/after a date."""
    return fetch_open_price(ticker, date_str)


@st.cache_data(ttl=3600, show_spinner="Fetching opening prices...")
def fetch_opening_prices_batch(tickers: tuple, date_str: str) -> dict[str, float | None]:
    """Opening prices for multiple tickers on a specific date."""
    return {t: fetch_open_price(t, date_str) for t in tickers}


# ── Stock metadata ──────────────────────────────────────────────────────────

def fetch_stock_info(ticker: str) -> dict:
    """Fetch name (and, if available, sector/industry) for a ticker."""
    return _fetch_stock_info_cached(ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_stock_info_cached(ticker: str) -> dict:
    """Company name from Yahoo chart meta. Sector/industry/beta not available
    via the public chart endpoint — returned empty (user can fill manually)."""
    ns = _ensure_ns_suffix(ticker)
    name = ticker
    res = _yahoo_chart(ns, {"range": "1d", "interval": "1d"})
    if res:
        meta = res.get("meta") or {}
        name = meta.get("longName") or meta.get("shortName") or ticker
    return {"beta": None, "dividend_yield": 0, "sector": "", "industry": "", "long_name": name}


def fetch_stock_info_batch(tickers: list[str]) -> dict[str, dict]:
    """Fetch info for multiple tickers (each individually cached)."""
    return {t: _fetch_stock_info_cached(t) for t in tickers}


# ── Calculations ────────────────────────────────────────────────────────────

def calculate_units(weightage: float, total_amount: float, buy_price: float) -> float:
    """Calculate number of units: (weightage% * total_amount) / buy_price."""
    if buy_price <= 0:
        return 0
    return round((weightage / 100 * total_amount) / buy_price, 4)


def calculate_invested_amount(units: float, buy_price: float) -> float:
    return round(units * buy_price, 2)


def calculate_market_value(units: float, current_price: float) -> float:
    return round(units * current_price, 2)


def calculate_pnl(market_value: float, invested: float) -> float:
    return round(market_value - invested, 2)


def calculate_pnl_pct(pnl: float, invested: float) -> float:
    if invested <= 0:
        return 0
    return round(pnl / invested * 100, 2)


def calculate_days_held(buy_date_str: str) -> int:
    """Days from buy_date to today."""
    if not buy_date_str:
        return 0
    try:
        buy_dt = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
        return (date.today() - buy_dt).days
    except (ValueError, TypeError):
        return 0


def calculate_xirr(buy_date_str: str, buy_price: float, units: float,
                   current_price: float, exit_date_str: str = None) -> float | None:
    """
    Calculate XIRR (annualized return) for a single holding.
    Cash flows: -invested on buy_date, +market_value on today/exit_date.
    """
    if not buy_date_str or buy_price <= 0 or units <= 0:
        return None

    try:
        from pyxirr import xirr as pyxirr_xirr
        buy_dt = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(exit_date_str, "%Y-%m-%d").date() if exit_date_str else date.today()

        if (end_dt - buy_dt).days < 1:
            return None

        invested = units * buy_price
        current_val = units * current_price

        dates = [buy_dt, end_dt]
        amounts = [-invested, current_val]

        result = pyxirr_xirr(dates, amounts)
        if result is not None and not np.isnan(result):
            return round(result * 100, 2)
        return None
    except Exception:
        # Fallback: simple annualized return
        try:
            buy_dt = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(exit_date_str, "%Y-%m-%d").date() if exit_date_str else date.today()
            days = (end_dt - buy_dt).days
            if days < 1:
                return None
            invested = units * buy_price
            current_val = units * current_price
            total_return = (current_val - invested) / invested
            annualized = ((1 + total_return) ** (365 / days) - 1) * 100
            return round(annualized, 2)
        except Exception:
            return None


def calculate_portfolio_volatility(tickers: list[str], weightages: list[float],
                                   period: str = "1y") -> float | None:
    """Calculate portfolio standard deviation (annualized) from daily returns."""
    return _calc_vol_cached(tuple(tickers), tuple(weightages), period)


@st.cache_data(ttl=3600, show_spinner=False)
def _calc_vol_cached(tickers: tuple, weightages: tuple, period: str) -> float | None:
    if not tickers:
        return None

    # Fetch 1y daily closes per ticker via direct Yahoo requests
    series = {}
    for t in tickers:
        res = _yahoo_chart(_ensure_ns_suffix(t), {"range": period, "interval": "1d"})
        if not res:
            continue
        try:
            closes = res["indicators"]["quote"][0]["close"]
            ts = res.get("timestamp") or []
            s = pd.Series(closes, index=pd.to_datetime(ts, unit="s")).dropna()
            if not s.empty:
                series[t] = s
        except Exception:
            continue

    if not series:
        return None

    try:
        closes_df = pd.DataFrame(series).dropna()
        returns = closes_df.pct_change(fill_method=None).dropna()
        if returns.empty:
            return None

        weights = np.array(list(weightages)[:len(returns.columns)], dtype=float) / 100
        if weights.sum() > 0:
            weights = weights / weights.sum()

        cov_matrix = returns.cov() * 252
        port_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        return round(float(np.sqrt(port_var)) * 100, 2)
    except Exception:
        return None


def calculate_weighted_beta(betas: list[float | None], weightages: list[float]) -> float | None:
    """Weighted average beta."""
    valid = [(b, w) for b, w in zip(betas, weightages) if b is not None]
    if not valid:
        return None
    total_w = sum(w for _, w in valid)
    if total_w == 0:
        return None
    return round(sum(b * w for b, w in valid) / total_w, 3)


def calculate_weighted_div_yield(yields: list[float], weightages: list[float]) -> float:
    """Weighted average dividend yield."""
    total_w = sum(weightages)
    if total_w == 0:
        return 0
    return round(sum(y * w for y, w in zip(yields, weightages)) / total_w, 2)


def get_sector_concentration(industries: list[str], weightages: list[float]) -> dict[str, float]:
    """Return sector -> total weightage mapping."""
    sector_map: dict[str, float] = {}
    for ind, w in zip(industries, weightages):
        key = ind if ind else "Unknown"
        sector_map[key] = sector_map.get(key, 0) + w
    return dict(sorted(sector_map.items(), key=lambda x: -x[1]))


# ── Mutual Fund helpers (MFAPI.in) ──────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def search_mutual_funds(query: str) -> list[dict]:
    """Search mutual fund schemes by name using MFAPI.in (free, no API key)."""
    if not query or len(query) < 2:
        return []
    try:
        resp = requests.get(
            f"https://api.mfapi.in/mf/search?q={requests.utils.quote(query)}",
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()  # [{schemeCode, schemeName}]
    except Exception:
        pass
    return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_mf_nav(scheme_code: int) -> dict:
    """Fetch latest NAV + metadata for a scheme from MFAPI.in."""
    empty = {"nav": 0.0, "nav_date": "", "fund_house": "",
             "scheme_category": "", "scheme_name": ""}
    try:
        resp = requests.get(
            f"https://api.mfapi.in/mf/{scheme_code}/latest", timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            nav_entry = data.get("data", [{}])[0]
            meta = data.get("meta", {})
            nav_val = nav_entry.get("nav", "0")
            return {
                "nav": round(float(nav_val), 4) if nav_val else 0.0,
                "nav_date": nav_entry.get("date", ""),
                "fund_house": meta.get("fund_house", ""),
                "scheme_category": meta.get("scheme_category", ""),
                "scheme_name": meta.get("scheme_name", ""),
            }
    except Exception:
        pass
    return empty


def fetch_mf_nav_batch(scheme_codes: list[int]) -> dict[int, dict]:
    """Fetch NAV for multiple scheme codes."""
    return {code: fetch_mf_nav(code) for code in scheme_codes}
