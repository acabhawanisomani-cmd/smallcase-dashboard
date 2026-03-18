"""Financial data fetching and calculations."""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from functools import lru_cache
import time

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


def fetch_live_data(tickers: list[str]) -> dict[str, dict]:
    """Fetch current price, previous close, day change, and % change for a list of tickers."""
    global _price_cache, _cache_time

    now = time.time()
    # Return cache if fresh
    missing = [t for t in tickers if t not in _price_cache] if (now - _cache_time < CACHE_TTL) else tickers

    if not missing:
        return {t: _price_cache.get(t, _empty_quote()) for t in tickers}

    ns_tickers = [_ensure_ns_suffix(t) for t in missing]
    raw_to_orig = dict(zip(ns_tickers, missing))

    try:
        data = yf.download(ns_tickers, period="2d", progress=False, threads=True)
    except Exception:
        return {t: _price_cache.get(t, _empty_quote()) for t in tickers}

    for ns_t, orig_t in raw_to_orig.items():
        try:
            # yf.download always returns MultiIndex columns: (Price, Ticker)
            if isinstance(data.columns, pd.MultiIndex):
                if len(ns_tickers) == 1:
                    # Columns are like ('Close', 'TICKER.NS') — droplevel to simplify
                    df = data.droplevel("Ticker", axis=1)
                else:
                    # Select this ticker's slice from the MultiIndex
                    df = data.xs(ns_t, level="Ticker", axis=1)
            else:
                df = data

            if df.empty or len(df) < 1:
                _price_cache[orig_t] = _empty_quote()
                continue

            current = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else current
            change = current - prev
            pct = (change / prev * 100) if prev != 0 else 0.0

            _price_cache[orig_t] = {
                "current_price": round(current, 2),
                "prev_close": round(prev, 2),
                "today_change": round(change, 2),
                "pct_change": round(pct, 2),
            }
        except Exception:
            _price_cache[orig_t] = _empty_quote()

    _cache_time = now
    return {t: _price_cache.get(t, _empty_quote()) for t in tickers}


def _empty_quote() -> dict:
    return {"current_price": 0, "prev_close": 0, "today_change": 0, "pct_change": 0}


def fetch_stock_info(ticker: str) -> dict:
    """Fetch beta, dividend yield, sector, industry for a ticker."""
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
    """Fetch info for multiple tickers."""
    results = {}
    for t in tickers:
        results[t] = fetch_stock_info(t)
    return results


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
    if not tickers:
        return None

    ns_tickers = [_ensure_ns_suffix(t) for t in tickers]
    try:
        data = yf.download(ns_tickers, period=period, progress=False, threads=True)
        if data.empty:
            return None

        closes = data["Close"]
        # Handle MultiIndex columns from yf.download
        if isinstance(closes, pd.DataFrame) and isinstance(closes.columns, pd.MultiIndex):
            closes.columns = closes.columns.droplevel(0)
        if isinstance(closes, pd.Series):
            closes = closes.to_frame()

        returns = closes.pct_change().dropna()
        if returns.empty:
            return None

        # Align weightages
        weights = np.array(weightages[:len(returns.columns)]) / 100
        if weights.sum() > 0:
            weights = weights / weights.sum()

        cov_matrix = returns.cov() * 252  # Annualized
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
