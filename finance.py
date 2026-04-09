"""Financial data fetching and calculations."""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from functools import lru_cache
import time
import streamlit as st

# Cache for live prices (refreshed per session)
_price_cache: dict[str, dict] = {}
_cache_time: float = 0
CACHE_TTL = 300  # 5 minutes


def _ensure_ns_suffix(ticker: str) -> str:
    """Add .NS suffix for NSE tickers if not present."""
    t = ticker.strip().upper()
    if not t.endswith(".NS") and not t.endswith(".BO"):
        t += ".NS"
    return t


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_open_price(ticker: str, target_date: str) -> float | None:
    """
    Fetch the opening price of a stock on a specific date.
    If the date is a holiday/weekend, fetches the next trading day's open.
    Returns None if data can't be fetched.
    """
    ns = _ensure_ns_suffix(ticker)
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        # Fetch a few extra days to handle weekends/holidays
        start = dt
        end = dt + timedelta(days=7)
        data = yf.download(ns, start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"),
                          progress=False)
        if data.empty:
            return None

        # Handle MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            data = data.droplevel("Ticker", axis=1)

        # Get the first available trading day's open price (on or after target date)
        if not data.empty:
            return round(float(data["Open"].iloc[0]), 2)
        return None
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_open_prices_batch(tickers: list[str], target_date: str) -> dict[str, float | None]:
    """Fetch opening prices for multiple tickers on a specific date."""
    if not tickers:
        return {}

    ns_tickers = [_ensure_ns_suffix(t) for t in tickers]
    ns_to_orig = dict(zip(ns_tickers, tickers))

    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        start = dt
        end = dt + timedelta(days=7)
        data = yf.download(ns_tickers, start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"),
                          progress=False, threads=True)
        if data.empty:
            return {t: None for t in tickers}

        results = {}
        for ns_t, orig_t in ns_to_orig.items():
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if len(ns_tickers) == 1:
                        df = data.droplevel("Ticker", axis=1)
                    else:
                        df = data.xs(ns_t, level="Ticker", axis=1)
                else:
                    df = data

                if not df.empty:
                    results[orig_t] = round(float(df["Open"].iloc[0]), 2)
                else:
                    results[orig_t] = None
            except Exception:
                results[orig_t] = None

        return results
    except Exception:
        return {t: None for t in tickers}


def fetch_live_data(tickers: list[str]) -> dict[str, dict]:
    """Fetch current price, previous close, day change, and % change for a list of tickers."""
    # Use Streamlit cache — converts list to tuple for hashability
    return _fetch_live_data_cached(tuple(sorted(set(tickers))))


@st.cache_data(ttl=300, show_spinner="Fetching live prices...")  # Cache 5 min
def _fetch_live_data_cached(tickers: tuple) -> dict[str, dict]:
    """Cached live price fetch — only calls yfinance every 5 minutes."""
    result = {}
    ns_tickers = [_ensure_ns_suffix(t) for t in tickers]
    raw_to_orig = dict(zip(ns_tickers, tickers))

    try:
        data = yf.download(list(ns_tickers), period="2d", progress=False, threads=True)
    except Exception:
        return {t: _empty_quote() for t in tickers}

    for ns_t, orig_t in raw_to_orig.items():
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if len(ns_tickers) == 1:
                    df = data.droplevel("Ticker", axis=1)
                else:
                    df = data.xs(ns_t, level="Ticker", axis=1)
            else:
                df = data

            if df.empty or len(df) < 1:
                result[orig_t] = _empty_quote()
                continue

            current = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else current
            change = current - prev
            pct = (change / prev * 100) if prev != 0 else 0.0

            result[orig_t] = {
                "current_price": round(current, 2),
                "prev_close": round(prev, 2),
                "today_change": round(change, 2),
                "pct_change": round(pct, 2),
            }
        except Exception:
            result[orig_t] = _empty_quote()

    return result


def _empty_quote() -> dict:
    return {"current_price": 0, "prev_close": 0, "today_change": 0, "pct_change": 0}


def fetch_stock_info(ticker: str) -> dict:
    """Fetch beta, dividend yield, sector, industry for a ticker."""
    return _fetch_stock_info_cached(ticker)


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def _fetch_stock_info_cached(ticker: str) -> dict:
    """Cached version - avoids repeated yfinance calls."""
    ns = _ensure_ns_suffix(ticker)
    try:
        info = yf.Ticker(ns).info
        return {
            "beta": info.get("beta", None),
            "dividend_yield": info.get("dividendYield", 0) or 0,
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "long_name": info.get("longName", ticker),
        }
    except Exception:
        return {"beta": None, "dividend_yield": 0, "sector": "", "industry": "", "long_name": ticker}


def fetch_stock_info_batch(tickers: list[str]) -> dict[str, dict]:
    """Fetch info for multiple tickers (each individually cached)."""
    results = {}
    for t in tickers:
        results[t] = _fetch_stock_info_cached(t)
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_opening_price(ticker: str, date_str: str) -> float | None:
    """Fetch the opening price for a ticker on a specific date."""
    ns = _ensure_ns_suffix(ticker)
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Fetch a few days around the target date to handle holidays
        start = dt - timedelta(days=3)
        end = dt + timedelta(days=3)
        data = yf.download(ns, start=start.strftime("%Y-%m-%d"),
                           end=end.strftime("%Y-%m-%d"), progress=False)
        if data.empty:
            return None
        # Handle MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            data = data.droplevel("Ticker", axis=1)
        # Find the exact date or the next available trading day
        data.index = pd.to_datetime(data.index).date
        if dt in data.index:
            return round(float(data.loc[dt, "Open"]), 2)
        # Find next trading day after target date
        future = data[data.index >= dt]
        if not future.empty:
            return round(float(future.iloc[0]["Open"]), 2)
        return None
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner="Fetching opening prices...")
def fetch_opening_prices_batch(tickers: tuple, date_str: str) -> dict[str, float | None]:
    """Fetch opening prices for multiple tickers on a specific date."""
    result = {}
    for t in tickers:
        result[t] = fetch_opening_price(t, date_str)
    return result


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
    # Convert to tuples for caching
    return _calc_vol_cached(tuple(tickers), tuple(weightages), period)


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def _calc_vol_cached(tickers: tuple, weightages: tuple, period: str) -> float | None:
    if not tickers:
        return None

    ns_tickers = [_ensure_ns_suffix(t) for t in tickers]
    try:
        data = yf.download(ns_tickers, period=period, progress=False, threads=True)
        if data.empty:
            return None

        closes = data["Close"]
        if isinstance(closes, pd.DataFrame) and isinstance(closes.columns, pd.MultiIndex):
            closes.columns = closes.columns.droplevel(0)
        if isinstance(closes, pd.Series):
            closes = closes.to_frame()

        returns = closes.pct_change(fill_method=None).dropna()
        if returns.empty:
            return None

        weights = np.array(list(weightages)[:len(returns.columns)]) / 100
        if weights.sum() > 0:
            weights = weights / weights.sum()

        cov_matrix = returns.cov() * 252
        port_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        return round(np.sqrt(port_var) * 100, 2)
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
