"""
Master Smallcase Dashboard
A professional portfolio management tool for Research Analysts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import database as db
import finance as fin

# ── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Smallcase Dashboard",
    page_icon="🙏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Password Protection ────────────────────────────────────────────────────

def check_password():
    """Returns True if the user has entered the correct password."""

    def password_entered():
        """Check if entered password is correct."""
        if st.session_state.get("password") == st.secrets.get("APP_PASSWORD", "Hare@Krishna108"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show login screen
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; min-height: 60vh;">
        <div style="text-align: center;">
            <h1 style="font-size: 4rem;">🙏</h1>
            <h2>Smallcase Dashboard</h2>
            <p style="color: #888;">Enter password to continue</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.text_input("Password", type="password", key="password", on_change=password_entered)
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Incorrect password")
    return False


if not check_password():
    st.stop()

# ── Krishna-Themed Custom CSS ──────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Main background: Deep Krishna blue with subtle radial glow ── */
    .stApp {
        background: radial-gradient(ellipse at 20% 50%, #0a1628 0%, #060d1a 40%, #030812 100%) !important;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background:
            radial-gradient(circle at 85% 15%, rgba(212, 175, 55, 0.04) 0%, transparent 40%),
            radial-gradient(circle at 10% 80%, rgba(0, 128, 128, 0.05) 0%, transparent 35%),
            radial-gradient(circle at 50% 50%, rgba(30, 60, 114, 0.08) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Sidebar: Deep royal blue with gold top accent ── */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1a3a 0%, #091225 40%, #060d1a 100%) !important;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
    }
    div[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #d4af37, #f0d060, #d4af37);
    }

    /* ── Metric cards: Peacock feather inspired gradient ── */
    .metric-card {
        background: linear-gradient(135deg, #0b1a3a 0%, #0f2244 50%, #112a4a 100%);
        border-radius: 14px;
        padding: 22px;
        text-align: center;
        border: 1px solid rgba(212, 175, 55, 0.2);
        margin-bottom: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(212, 175, 55, 0.08);
        position: relative;
        overflow: hidden;
    }
    .metric-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.5), transparent);
    }
    .metric-card h3 {
        color: #c4a44a;
        font-size: 12px;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    .metric-card .value {
        font-size: 28px;
        font-weight: 700;
        margin: 10px 0 0;
    }

    /* ── P/L colors ── */
    .profit { color: #00e676 !important; }
    .loss { color: #ff5252 !important; }
    .neutral { color: #e8dcc8 !important; }

    /* ── Warning flags ── */
    .flag-warning {
        background: rgba(255, 82, 82, 0.1);
        border: 1px solid rgba(255, 82, 82, 0.4);
        border-radius: 8px;
        padding: 10px 15px;
        margin: 5px 0;
        color: #ff8a80;
    }

    /* ── Tab styling: Royal blue with gold hover ── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #0b1a3a, #0f2244) !important;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        border: 1px solid rgba(212, 175, 55, 0.15) !important;
        color: #c4a44a !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        border-color: rgba(212, 175, 55, 0.4) !important;
        background: linear-gradient(135deg, #0f2244, #153060) !important;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #d4af37 !important;
        color: #f0d060 !important;
    }

    /* ── Headings: Gold color ── */
    h1, h2, h3 {
        color: #e8dcc8 !important;
    }
    h1 { text-shadow: 0 0 30px rgba(212, 175, 55, 0.15); }

    /* ── Data tables ── */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(212, 175, 55, 0.12) !important;
    }

    /* ── Buttons: Gold accent ── */
    .stButton > button {
        background: linear-gradient(135deg, #0f2244 0%, #1a3366 100%) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        color: #e8dcc8 !important;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        border-color: #d4af37 !important;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
        background: linear-gradient(135deg, #1a3366 0%, #244080 100%) !important;
    }

    /* ── Input fields ── */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-color: rgba(212, 175, 55, 0.2) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: rgba(212, 175, 55, 0.5) !important;
        box-shadow: 0 0 8px rgba(212, 175, 55, 0.15) !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #0b1a3a, #0f2244) !important;
        border: 1px solid rgba(212, 175, 55, 0.15) !important;
        border-radius: 10px !important;
        color: #c4a44a !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #060d1a; }
    ::-webkit-scrollbar-thumb { background: rgba(212, 175, 55, 0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(212, 175, 55, 0.5); }

    /* ── Radio buttons in sidebar ── */
    div[data-testid="stSidebar"] .stRadio label {
        color: #c4a44a !important;
    }

    /* ── Separator lines ── */
    hr {
        border-color: rgba(212, 175, 55, 0.12) !important;
    }

    /* ── Om symbol watermark ── */
    .krishna-watermark {
        position: fixed;
        bottom: 20px;
        right: 30px;
        font-size: 60px;
        opacity: 0.04;
        color: #d4af37;
        pointer-events: none;
        z-index: 0;
        font-family: serif;
    }
</style>

<!-- Subtle Om watermark -->
<div class="krishna-watermark">&#x0950;</div>
""", unsafe_allow_html=True)


# ── Helper Functions ────────────────────────────────────────────────────────

def metric_card(label: str, value: str, css_class: str = "neutral"):
    st.markdown(f"""
    <div class="metric-card">
        <h3>{label}</h3>
        <div class="value {css_class}">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def format_inr(amount: float) -> str:
    """Format number in Indian Rupee style."""
    if abs(amount) >= 1e7:
        return f"₹{amount / 1e7:,.2f} Cr"
    if abs(amount) >= 1e5:
        return f"₹{amount / 1e5:,.2f} L"
    return f"₹{amount:,.2f}"


def color_pnl(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return "color: #00e676"
        elif val < 0:
            return "color: #ff5252"
    return ""


def build_holdings_table(holdings_df: pd.DataFrame, total_amount: float,
                         is_design: bool = False) -> pd.DataFrame:
    """Build the full calculated holdings table with live data."""
    if holdings_df.empty:
        return pd.DataFrame()

    tickers = holdings_df["ticker"].tolist()
    live_data = fin.fetch_live_data(tickers)

    rows = []
    for _, h in holdings_df.iterrows():
        t = h["ticker"]
        ld = live_data.get(t, fin._empty_quote())
        current_price = ld["current_price"] if ld["current_price"] > 0 else h["buy_price"]

        if is_design:
            units = fin.calculate_units(h["weightage"], total_amount, current_price)
            buy_price = current_price
        else:
            units = h["units"]
            buy_price = h["buy_price"]

        invested = fin.calculate_invested_amount(units, buy_price)
        mkt_val = fin.calculate_market_value(units, current_price)
        pnl = fin.calculate_pnl(mkt_val, invested)
        pnl_pct = fin.calculate_pnl_pct(pnl, invested)
        days = fin.calculate_days_held(h["buy_date"]) if not is_design else 0
        xirr = fin.calculate_xirr(h["buy_date"], buy_price, units, current_price) if not is_design else None

        sl = float(h["stop_loss"]) if h.get("stop_loss") and float(h["stop_loss"]) > 0 else 0.0
        sl_triggered = sl > 0 and current_price <= sl

        rows.append({
            "ID": h["id"],
            "Scrip Name": h["scrip_name"],
            "Ticker": t,
            "Industry": h["industry"],
            "Weightage %": h["weightage"],
            "Units": round(units, 2),
            "Buy Date": h["buy_date"] if h["buy_date"] else "",
            "Buy Price": round(buy_price, 2),
            "Current Price": current_price,
            "Invested Amount": invested,
            "Market Value": mkt_val,
            "P/L": pnl,
            "P/L %": pnl_pct,
            "Days Held": days,
            "XIRR %": xirr if xirr is not None else "",
            "Today Chg": ld["today_change"],
            "% Chg": ld["pct_change"],
            "Stop Loss": sl if sl > 0 else "",
            "🚨 SL Hit": "🚨 SL HIT" if sl_triggered else "",
            "_sl_triggered": sl_triggered,   # internal flag for row highlight
            "Exit Date": h["exit_date"] if h["exit_date"] else "",
            "Exit Price": h["exit_price"] if h["exit_price"] else "",
        })

    return pd.DataFrame(rows)


# ── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.markdown("""
<div style="text-align:center; padding: 10px 0 5px;">
    <span style="font-size: 36px;">🙏</span>
    <h2 style="margin: 5px 0 0; color: #d4af37 !important; font-size: 22px;
               text-shadow: 0 0 20px rgba(212,175,55,0.2);">
        Smallcase Manager
    </h2>
    <p style="color: rgba(212,175,55,0.5); font-size: 11px; margin: 2px 0 0;
              letter-spacing: 2px;">
        कर्मण्येवाधिकारस्ते
    </p>
</div>
""", unsafe_allow_html=True)

# Create new smallcase
with st.sidebar.expander("➕ Create New Smallcase", expanded=False):
    with st.form("new_sc_form"):
        sc_name = st.text_input("Smallcase Name")
        sc_desc = st.text_input("Description")
        sc_amount = st.number_input("Total Investable Amount (₹)", min_value=0.0,
                                    value=100000.0, step=10000.0)
        sc_design = st.checkbox("Design Mode (Simulation)", value=False)
        submitted = st.form_submit_button("Create")
        if submitted and sc_name:
            try:
                db.create_smallcase(sc_name, sc_desc, sc_amount, sc_design)
                st.success(f"Created: {sc_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# List all smallcases
all_sc = db.get_all_smallcases()
sc_names = [s["name"] for s in all_sc]

if not all_sc:
    st.sidebar.info("No smallcases yet. Create one above.")

# Navigation
st.sidebar.markdown("---")
nav = st.sidebar.radio(
    "Navigate",
    ["🏠 Master Dashboard"] + [f"{'🧪' if s['is_design_mode'] else '📁'} {s['name']}" for s in all_sc],
    index=0,
)


# ── Master Dashboard ───────────────────────────────────────────────────────

def render_master_dashboard():
    st.title("Master Smallcase Dashboard")
    st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    if not all_sc:
        st.info("Create your first smallcase from the sidebar to get started.")
        return

    # Aggregate data across all live (non-design) smallcases
    total_invested = 0
    total_market_val = 0
    total_unrealized = 0
    total_realized = 0
    sector_data = {}
    sc_summaries = []

    for sc in all_sc:
        if sc["is_design_mode"]:
            continue
        # Realized P/L from exited holdings (even if the smallcase is now empty)
        realized = db.get_realized_pnl(sc["id"])["total_realized"]

        holdings = db.get_holdings(sc["id"])
        if holdings.empty and realized == 0:
            continue

        if not holdings.empty:
            table = build_holdings_table(holdings, sc["total_investable_amount"])
        else:
            table = pd.DataFrame()

        if not table.empty:
            inv = table["Invested Amount"].sum()
            mv = table["Market Value"].sum()
            pl = table["P/L"].sum()
        else:
            inv = mv = pl = 0

        total_invested += inv
        total_market_val += mv
        total_unrealized += pl
        total_realized += realized

        # Sector aggregation
        if not table.empty:
            for _, row in table.iterrows():
                ind = row["Industry"] if row["Industry"] else "Unknown"
                sector_data[ind] = sector_data.get(ind, 0) + row["Market Value"]

        combined_pl = pl + realized
        sc_summaries.append({
            "Smallcase": sc["name"],
            "Invested": inv,
            "Market Value": mv,
            "Unrealized P/L": pl,
            "Realized P/L": realized,
            "Total P/L": combined_pl,
            "Total P/L %": round(combined_pl / inv * 100, 2) if inv > 0 else 0,
            "Stocks": len(table) if not table.empty else 0,
        })

    # Top metric cards
    total_pnl = total_unrealized + total_realized
    pnl_pct = round(total_pnl / total_invested * 100, 2) if total_invested > 0 else 0
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Total Invested", format_inr(total_invested))
    with col2:
        metric_card("Current Value", format_inr(total_market_val),
                     "profit" if total_market_val >= total_invested else "loss")
    with col3:
        metric_card("Unrealized P/L", format_inr(total_unrealized),
                     "profit" if total_unrealized >= 0 else "loss")
    with col4:
        metric_card("Realized P/L", format_inr(total_realized),
                     "profit" if total_realized >= 0 else "loss")
    with col5:
        metric_card("Total P/L", f"{format_inr(total_pnl)} ({pnl_pct}%)",
                     "profit" if total_pnl >= 0 else "loss")

    st.markdown("---")

    # Smallcase performance table
    if sc_summaries:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("Smallcase Performance")
            sum_df = pd.DataFrame(sc_summaries)
            st.dataframe(
                sum_df.style.map(color_pnl,
                                 subset=["Unrealized P/L", "Realized P/L",
                                         "Total P/L", "Total P/L %"])
                     .format({
                         "Invested": "₹{:,.0f}",
                         "Market Value": "₹{:,.0f}",
                         "Unrealized P/L": "₹{:,.0f}",
                         "Realized P/L": "₹{:,.0f}",
                         "Total P/L": "₹{:,.0f}",
                         "Total P/L %": "{:.2f}%",
                     }),
                width="stretch", hide_index=True,
            )

        with col_right:
            st.subheader("Sector Exposure")
            if sector_data:
                fig = px.pie(
                    names=list(sector_data.keys()),
                    values=list(sector_data.values()),
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_traces(textposition='inside', textinfo='percent',
                                  hoverinfo='label+percent+value')
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0",
                    height=450,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(
                        font=dict(size=9),
                        orientation="h",
                        yanchor="top",
                        y=-0.1,
                        xanchor="center",
                        x=0.5,
                    ),
                )
                st.plotly_chart(fig, use_container_width=True)

    # Capital allocation bar chart
    if sc_summaries:
        st.subheader("Capital Allocation")
        alloc_df = pd.DataFrame(sc_summaries)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=alloc_df["Smallcase"], y=alloc_df["Invested"],
            name="Invested", marker_color="#5c6bc0"
        ))
        fig.add_trace(go.Bar(
            x=alloc_df["Smallcase"], y=alloc_df["Market Value"],
            name="Market Value", marker_color="#26a69a"
        ))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            height=350,
            margin=dict(t=20, b=40),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#2d2d44"),
        )
        st.plotly_chart(fig, width="stretch")


# ── Individual Smallcase View ──────────────────────────────────────────────

def render_smallcase(sc: dict):
    sc_id = sc["id"]
    is_design = bool(sc["is_design_mode"])

    # Header
    mode_badge = "🧪 DESIGN MODE" if is_design else "🟢 LIVE"
    st.title(f"{sc['name']}  ·  {mode_badge}")
    st.caption(sc["description"])

    # Settings row
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([2, 1, 1, 1, 1])
    with col_s1:
        new_amount = st.number_input(
            "Total Investable Amount (₹)",
            value=float(sc["total_investable_amount"]),
            min_value=0.0, step=10000.0, key=f"amt_{sc_id}",
        )
        if new_amount != sc["total_investable_amount"]:
            db.update_smallcase(sc_id, total_investable_amount=new_amount)
            st.rerun()
    with col_s2:
        if is_design:
            if st.button("🚀 Deploy (Go Live)", key=f"deploy_{sc_id}"):
                db.deploy_smallcase(sc_id)
                st.success("Deployed! Refresh to see changes.")
                st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📈 Sync to Market Value", key=f"sync_{sc_id}",
                         help="Update Investable Amount to current portfolio market value"):
                # Calculate current market value
                _h = db.get_holdings(sc_id)
                if not _h.empty:
                    _t = build_holdings_table(_h, new_amount)
                    if not _t.empty:
                        mv = round(_t["Market Value"].sum(), 2)
                        db.update_smallcase(sc_id, total_investable_amount=mv)
                        st.success(f"Investable Amount synced to ₹{mv:,.2f}")
                        st.rerun()
    with col_s3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Prices", key=f"refresh_{sc_id}"):
            st.cache_data.clear()
            st.rerun()
    with col_s4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧮 Recalc Units", key=f"recalc_{sc_id}",
                     help="Recalculate units for ALL holdings: (weightage% × Investable Amount) / buy_price. "
                          "Use this when Invested Amount doesn't match the smallcase platform."):
            _h = db.get_holdings(sc_id)
            if not _h.empty:
                updated = 0
                for _, h in _h.iterrows():
                    if h["buy_price"] > 0 and h["weightage"] > 0:
                        new_units = round((h["weightage"] / 100 * new_amount) / h["buy_price"], 4)
                        db.update_holding(int(h["id"]), units=new_units)
                        updated += 1
                st.success(f"Recalculated units for {updated} holdings against ₹{new_amount:,.2f}")
                st.rerun()
    with col_s5:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete", key=f"del_{sc_id}"):
            db.delete_smallcase(sc_id)
            st.rerun()

    total_amount = new_amount

    # ── Add Stock Form ──────────────────────────────────────────────────────
    with st.expander("➕ Add Stock", expanded=False):
        # Step 1: Ticker lookup (outside form for instant feedback)
        lookup_key = f"lookup_{sc_id}"
        lc1, lc2 = st.columns([3, 1])
        with lc1:
            ticker_input = st.text_input("Ticker (e.g., RELIANCE, TCS)", key=f"ticker_inp_{sc_id}")
        with lc2:
            st.markdown("<br>", unsafe_allow_html=True)
            lookup_clicked = st.button("🔍 Lookup", key=f"lookup_btn_{sc_id}")

        # Fetch and cache stock info in session_state
        if lookup_clicked and ticker_input:
            with st.spinner(f"Fetching info for {ticker_input.upper()}..."):
                info = fin.fetch_stock_info(ticker_input.strip())
                st.session_state[lookup_key] = {
                    "ticker": ticker_input.strip().upper(),
                    "name": info.get("long_name", ticker_input.strip().upper()),
                    "industry": info.get("industry", ""),
                    "sector": info.get("sector", ""),
                }

        # Pre-fill defaults from lookup
        looked_up = st.session_state.get(lookup_key, {})
        default_name = looked_up.get("name", "")
        default_industry = looked_up.get("industry", "")
        if looked_up.get("sector") and default_industry:
            default_industry = f"{looked_up['sector']} / {default_industry}"
        elif looked_up.get("sector"):
            default_industry = looked_up["sector"]

        if looked_up:
            st.success(f"Found: **{default_name}** — {default_industry}")

        # Step 2: Date picker outside form for auto-price fetch
        add_buy_date = st.date_input("Date of Buy (open price auto-fetched)",
                                      value=date.today(), key=f"add_date_{sc_id}")
        add_date_str = add_buy_date.strftime("%Y-%m-%d")

        # Auto-fetch opening price if we have a ticker
        add_fetched_price = 0.0
        add_liq_fetched = 0.0
        if looked_up.get("ticker"):
            add_fetched_price = fin.fetch_open_price(looked_up["ticker"], add_date_str) or 0.0
            add_liq_fetched = fin.fetch_open_price(db.RESIDUAL_TICKER, add_date_str) or 0.0
            if add_fetched_price > 0:
                st.success(f"📈 Opening price of **{looked_up['ticker']}** on **{add_date_str}**: **₹{add_fetched_price:,.2f}**")
            else:
                st.warning(f"Could not fetch price for {looked_up['ticker']} on {add_date_str}. Enter manually.")

        # Step 3: Form with pre-filled values
        with st.form(f"add_stock_{sc_id}"):
            c1, c2 = st.columns(2)
            with c1:
                scrip_name = st.text_input("Scrip Name", value=default_name)
                industry = st.text_input("Industry / Sector", value=default_industry)
                weightage = st.number_input("Target Weightage %", 0.0, 100.0, 5.0, 0.5)
            with c2:
                buy_price = st.number_input("Buy Price (₹)", 0.0, step=0.5,
                                             value=float(add_fetched_price),
                                             help="Auto-filled with opening price. Override if needed.")
                auto_calc = st.checkbox("Auto-calculate Units from Weightage", value=True)
                if not auto_calc:
                    manual_units = st.number_input("Manual Units", 0.0, step=1.0)

            sl_col1, sl_col2 = st.columns(2)
            with sl_col1:
                stop_loss_add = st.number_input(
                    "Stop Loss (₹) — optional",
                    min_value=0.0, step=0.5, value=0.0,
                    help="Row turns red on the dashboard if current price falls to or below this level. Leave 0 to skip."
                )
            with sl_col2:
                liq_exit_price = st.number_input(
                    "LIQUIDCASE exit price (₹) — auto-fetched",
                    min_value=0.0, step=0.1,
                    value=float(add_liq_fetched),
                    key=f"add_liq_ep_{sc_id}",
                    help="Auto-filled with LIQUIDCASE opening price on same date. Override if needed."
                )

            add_submitted = st.form_submit_button("Add Stock")
            if add_submitted and ticker_input:
                ticker_clean = ticker_input.strip().upper()
                if auto_calc:
                    price_for_calc = buy_price if buy_price > 0 else 1
                    units = fin.calculate_units(weightage, total_amount, price_for_calc)
                else:
                    units = manual_units

                db.add_holding(
                    smallcase_id=sc_id,
                    ticker=ticker_clean,
                    scrip_name=scrip_name if scrip_name else ticker_clean,
                    industry=industry,
                    weightage=weightage,
                    buy_price=buy_price,
                    buy_date=add_date_str,
                    units=units,
                    stop_loss=stop_loss_add,
                )

                # Auto-rebalance LIQUIDCASE
                if ticker_clean != db.RESIDUAL_TICKER:
                    rb = db.rebalance_residual(sc_id, total_amount,
                                               exit_price=liq_exit_price if liq_exit_price > 0 else None)
                    if rb:
                        st.info(f"🔄 LIQUIDCASE auto-adjusted: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                f"({rb['delta_units']:+.2f} units)")

                # Clear lookup cache
                st.session_state.pop(lookup_key, None)
                st.success(f"Added {ticker_clean} — {units} units")
                st.rerun()

    # ── CSV Upload & Rebalance ─────────────────────────────────────────────
    with st.expander("📤 Upload CSV to Rebalance", expanded=False):
        st.markdown("Upload your smallcase CSV to automatically rebalance the portfolio. "
                     "Format: `NSE Ticker, Weight, Segment (optional), Rationale (optional)`")
        st.markdown("> **How it works:** The system uses the **current portfolio market value** "
                     "as the rebalance base (just like the actual smallcase platform). "
                     "Buy/Sell happens at the opening price of the execution date.")

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key=f"csv_{sc_id}")

        if uploaded_file:
            try:
                csv_df = pd.read_csv(uploaded_file)
                # Normalize column names
                col_map = {}
                for c in csv_df.columns:
                    cl = c.strip().lower()
                    if "ticker" in cl:
                        col_map[c] = "ticker"
                    elif "weight" in cl:
                        col_map[c] = "weight"
                    elif "segment" in cl or "sector" in cl:
                        col_map[c] = "segment"
                    elif "rationale" in cl:
                        col_map[c] = "rationale"
                csv_df = csv_df.rename(columns=col_map)

                if "ticker" not in csv_df.columns or "weight" not in csv_df.columns:
                    st.error("CSV must have 'NSE Ticker' and 'Weight' columns.")
                else:
                    csv_df["ticker"] = csv_df["ticker"].str.strip().str.upper()
                    csv_df["weight"] = pd.to_numeric(csv_df["weight"], errors="coerce").fillna(0)

                    # Get current holdings and compute current market value
                    curr_holdings = db.get_holdings(sc_id)
                    curr_map = {}
                    current_market_value = 0.0
                    if not curr_holdings.empty:
                        # Build table to get live market values
                        _temp_table = build_holdings_table(curr_holdings, total_amount)
                        if not _temp_table.empty:
                            current_market_value = round(_temp_table["Market Value"].sum(), 2)

                        for _, h in curr_holdings.iterrows():
                            # Get live price from temp table
                            live_row = _temp_table[_temp_table["Ticker"] == h["ticker"]] if not _temp_table.empty else pd.DataFrame()
                            live_price = float(live_row["Current Price"].iloc[0]) if not live_row.empty else h["buy_price"]

                            curr_map[h["ticker"]] = {
                                "id": h["id"], "weight": h["weightage"],
                                "units": h["units"], "buy_price": h["buy_price"],
                                "scrip_name": h["scrip_name"], "industry": h["industry"],
                                "buy_date": h["buy_date"],
                                "current_price": live_price,
                                "market_value": h["units"] * live_price,
                            }

                    # Show rebalance base amount
                    st.markdown("### 💰 Rebalance Base Amount")
                    st.markdown("All new unit calculations will be based on this amount. "
                                "**Default = your Total Investable Amount.** Override only if "
                                "the smallcase platform shows a different value (e.g., after market movement).")

                    # Default to Total Investable Amount (not market value)
                    # because market value can be stale if existing units are wrong
                    default_base = total_amount if total_amount > 0 else current_market_value

                    rb_c1, rb_c2 = st.columns([2, 1])
                    with rb_c1:
                        rebalance_base = st.number_input(
                            "Rebalance Base Amount (₹)",
                            value=float(default_base),
                            min_value=0.0, step=100.0,
                            key=f"rebal_base_{sc_id}",
                            help="Defaults to Total Investable Amount. Override if smallcase platform shows a different value."
                        )
                    with rb_c2:
                        st.metric("Set Investable Amount", f"₹{total_amount:,.2f}")
                        st.metric("Current Market Value", f"₹{current_market_value:,.2f}")

                    csv_map = {}
                    for _, r in csv_df.iterrows():
                        csv_map[r["ticker"]] = {
                            "weight": round(r["weight"], 2),
                            "segment": r.get("segment", ""),
                        }

                    # Build diff table
                    all_tickers = sorted(set(list(curr_map.keys()) + list(csv_map.keys())))
                    diff_rows = []
                    for t in all_tickers:
                        old_wt = curr_map.get(t, {}).get("weight", 0)
                        new_wt = csv_map.get(t, {}).get("weight", 0)
                        change = round(new_wt - old_wt, 2)

                        if t not in curr_map and new_wt > 0:
                            action = "NEW BUY"
                        elif t not in csv_map or new_wt == 0:
                            action = "EXIT"
                        elif change > 0.01:
                            action = "ADD MORE"
                        elif change < -0.01:
                            action = "REDUCE"
                        else:
                            action = "NO CHANGE"

                        # Calculate expected units based on rebalance base
                        old_units = curr_map.get(t, {}).get("units", 0)
                        old_mkt_val = curr_map.get(t, {}).get("market_value", 0)

                        diff_rows.append({
                            "Ticker": t,
                            "Current Wt%": old_wt,
                            "New Wt%": new_wt,
                            "Change": change,
                            "Action": action,
                            "Current Units": round(old_units, 2),
                            "Current Value": round(old_mkt_val, 0),
                            "Target Value": round(new_wt / 100 * rebalance_base, 0),
                        })

                    diff_df = pd.DataFrame(diff_rows)

                    # Show diff with color coding
                    st.markdown("### Rebalance Preview")

                    def color_action(val):
                        colors = {
                            "NEW BUY": "color: #00e676; font-weight: bold",
                            "ADD MORE": "color: #69f0ae",
                            "REDUCE": "color: #ffca28",
                            "EXIT": "color: #ff5252; font-weight: bold",
                            "NO CHANGE": "color: #888",
                        }
                        return colors.get(val, "")

                    st.dataframe(
                        diff_df.style
                            .map(color_action, subset=["Action"])
                            .map(color_pnl, subset=["Change"])
                            .format({
                                "Current Wt%": "{:.1f}%", "New Wt%": "{:.1f}%", "Change": "{:+.1f}%",
                                "Current Units": "{:.2f}", "Current Value": "₹{:,.0f}", "Target Value": "₹{:,.0f}",
                            }),
                        width="stretch", hide_index=True,
                    )

                    changes = diff_df[diff_df["Action"] != "NO CHANGE"]
                    if changes.empty:
                        st.success("Portfolio already matches the CSV. No changes needed.")
                    else:
                        st.markdown("---")
                        st.markdown("**Execution Settings**")
                        st.markdown("> Buy/Sell prices = **opening price of the execution date** (next trading day).")

                        exec_date = st.date_input(
                            "Execution Date (next trading day)",
                            value=date.today(),
                            key=f"exec_date_{sc_id}",
                        )
                        exec_date_str = exec_date.strftime("%Y-%m-%d")

                        # Option to auto-fetch or manual prices
                        price_mode = st.radio(
                            "Price Mode",
                            ["Auto-fetch opening prices", "I'll enter prices manually"],
                            key=f"price_mode_{sc_id}",
                        )

                        fetched_prices = {}
                        if price_mode == "Auto-fetch opening prices":
                            action_tickers = changes["Ticker"].tolist()
                            if st.button("Fetch Opening Prices", key=f"fetch_op_{sc_id}"):
                                with st.spinner("Fetching opening prices..."):
                                    fetched_prices = fin.fetch_opening_prices_batch(
                                        tuple(action_tickers), exec_date_str
                                    )
                                    st.session_state[f"fetched_prices_{sc_id}"] = fetched_prices

                            fetched_prices = st.session_state.get(f"fetched_prices_{sc_id}", {})
                            if fetched_prices:
                                price_df = pd.DataFrame([
                                    {"Ticker": t, "Opening Price": f"₹{p:,.2f}" if p else "N/A"}
                                    for t, p in fetched_prices.items()
                                ])
                                st.dataframe(price_df, width="stretch", hide_index=True)

                                missing = [t for t, p in fetched_prices.items() if p is None]
                                if missing:
                                    st.warning(f"Could not fetch prices for: {', '.join(missing)}. "
                                              f"Enter manually below or try a different date.")

                        # Manual price overrides
                        manual_prices = {}
                        need_manual = []
                        for _, row in changes.iterrows():
                            t = row["Ticker"]
                            fp = fetched_prices.get(t)
                            if price_mode == "I'll enter prices manually" or fp is None:
                                need_manual.append(t)

                        if need_manual:
                            st.markdown("**Enter prices manually:**")
                            cols = st.columns(min(3, len(need_manual)))
                            for i, t in enumerate(need_manual):
                                with cols[i % len(cols)]:
                                    manual_prices[t] = st.number_input(
                                        f"{t} price (₹)", 0.0, step=0.5,
                                        key=f"mp_{sc_id}_{t}",
                                    )

                        # Merge prices: fetched + manual overrides
                        final_prices = {**fetched_prices, **{t: p for t, p in manual_prices.items() if p > 0}}

                        # Apply button
                        all_priced = all(final_prices.get(row["Ticker"]) and final_prices[row["Ticker"]] > 0
                                         for _, row in changes.iterrows())

                        if all_priced:
                            # Show what will happen with exact unit calculations
                            st.markdown("### 📋 Execution Summary")
                            exec_rows = []
                            for _, row in changes.iterrows():
                                t = row["Ticker"]
                                action = row["Action"]
                                new_wt = row["New Wt%"]
                                price = final_prices[t]
                                target_value = new_wt / 100 * rebalance_base
                                target_units = round(target_value / price, 4) if price > 0 else 0

                                if action == "NEW BUY":
                                    exec_rows.append({"Ticker": t, "Action": action,
                                        "Units": f"+{target_units:.4f}", "Price": f"₹{price:,.2f}",
                                        "Amount": f"₹{target_value:,.2f}"})
                                elif action == "EXIT":
                                    h = curr_map[t]
                                    exec_rows.append({"Ticker": t, "Action": action,
                                        "Units": f"-{h['units']:.4f}", "Price": f"₹{price:,.2f}",
                                        "Amount": f"₹{h['units'] * price:,.2f}"})
                                elif action == "ADD MORE":
                                    h = curr_map[t]
                                    add_units = round(target_units - h["units"], 4)
                                    if add_units > 0:
                                        exec_rows.append({"Ticker": t, "Action": f"BUY +{row['Change']:.1f}%",
                                            "Units": f"+{add_units:.4f}", "Price": f"₹{price:,.2f}",
                                            "Amount": f"₹{add_units * price:,.2f}"})
                                    else:
                                        exec_rows.append({"Ticker": t, "Action": f"SELL {row['Change']:.1f}%",
                                            "Units": f"{add_units:.4f}", "Price": f"₹{price:,.2f}",
                                            "Amount": f"₹{abs(add_units) * price:,.2f}"})
                                elif action == "REDUCE":
                                    h = curr_map[t]
                                    sell_units = round(h["units"] - target_units, 4)
                                    exec_rows.append({"Ticker": t, "Action": f"SELL {abs(row['Change']):.1f}%",
                                        "Units": f"-{sell_units:.4f}", "Price": f"₹{price:,.2f}",
                                        "Amount": f"₹{sell_units * price:,.2f}"})

                            exec_df = pd.DataFrame(exec_rows)
                            st.dataframe(exec_df.style.map(color_action, subset=["Action"]),
                                         width="stretch", hide_index=True)

                            if st.button("✅ Apply Rebalance", key=f"apply_rebal_{sc_id}", type="primary"):
                                applied = []
                                for _, row in changes.iterrows():
                                    t = row["Ticker"]
                                    action = row["Action"]
                                    new_wt = row["New Wt%"]
                                    price = final_prices[t]

                                    # Calculate target units based on rebalance base
                                    target_value = new_wt / 100 * rebalance_base
                                    target_units = round(target_value / price, 4) if price > 0 else 0

                                    if action == "NEW BUY":
                                        # Fetch stock info for name/industry
                                        info = fin.fetch_stock_info(t)
                                        segment = csv_map.get(t, {}).get("segment", "")
                                        industry = segment if segment else (
                                            f"{info['sector']} / {info['industry']}" if info["sector"] else info["industry"]
                                        )
                                        db.add_holding(
                                            smallcase_id=sc_id,
                                            ticker=t,
                                            scrip_name=info.get("long_name", t),
                                            industry=industry,
                                            weightage=new_wt,
                                            buy_price=price,
                                            buy_date=exec_date_str,
                                            units=target_units,
                                        )
                                        applied.append(f"BUY {t}: {new_wt}% @ ₹{price:,.2f} ({target_units:.4f} units)")

                                    elif action == "EXIT":
                                        h = curr_map[t]
                                        db.exit_holding(h["id"], price, exec_date_str)
                                        applied.append(f"EXIT {t}: sold {h['units']:.4f} units @ ₹{price:,.2f}")

                                    elif action == "ADD MORE":
                                        h = curr_map[t]
                                        old_units = h["units"]
                                        old_bp = h["buy_price"]
                                        add_units = round(target_units - old_units, 4)

                                        if add_units > 0:
                                            # Buying more — average up/down
                                            total_units = round(old_units + add_units, 4)
                                            avg_price = round(
                                                (old_units * old_bp + add_units * price) / total_units, 2
                                            ) if total_units > 0 else price

                                            db.update_holding(h["id"],
                                                              weightage=new_wt,
                                                              units=total_units,
                                                              buy_price=avg_price)

                                            conn = db.get_connection()
                                            conn.execute(
                                                "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
                                                "VALUES (?, ?, ?, 'BUY', ?, ?, ?)",
                                                (h["id"], sc_id, t, add_units, price, exec_date_str)
                                            )
                                            conn.commit()
                                            conn.close()
                                            applied.append(f"ADD {t}: +{add_units:.4f} units @ ₹{price:,.2f}, avg ₹{avg_price:,.2f}")
                                        else:
                                            # Actually need to sell (market moved, target units < current)
                                            sell_units = abs(add_units)
                                            new_total = round(old_units - sell_units, 4)
                                            db.update_holding(h["id"],
                                                              weightage=new_wt,
                                                              units=new_total)

                                            conn = db.get_connection()
                                            conn.execute(
                                                "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
                                                "VALUES (?, ?, ?, 'SELL', ?, ?, ?)",
                                                (h["id"], sc_id, t, sell_units, price, exec_date_str)
                                            )
                                            conn.commit()
                                            conn.close()
                                            applied.append(f"ADJUST {t}: sold {sell_units:.4f} units @ ₹{price:,.2f} (market value adjustment)")

                                    elif action == "REDUCE":
                                        h = curr_map[t]
                                        old_units = h["units"]
                                        sell_units = round(old_units - target_units, 4)

                                        db.update_holding(h["id"],
                                                          weightage=new_wt,
                                                          units=target_units)

                                        conn = db.get_connection()
                                        conn.execute(
                                            "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
                                            "VALUES (?, ?, ?, 'SELL', ?, ?, ?)",
                                            (h["id"], sc_id, t, sell_units, price, exec_date_str)
                                        )
                                        conn.commit()
                                        conn.close()
                                        applied.append(f"REDUCE {t}: {h['weight']}% → {new_wt}%, sold {sell_units:.4f} units @ ₹{price:,.2f}")

                                # Update investable amount to rebalance base
                                db.update_smallcase(sc_id, total_investable_amount=rebalance_base)

                                # Clear cached prices
                                st.session_state.pop(f"fetched_prices_{sc_id}", None)
                                st.cache_data.clear()

                                st.success(f"✅ Rebalance applied! Investable amount updated to ₹{rebalance_base:,.2f}")
                                for a in applied:
                                    st.markdown(f"- {a}")
                                st.rerun()
                        else:
                            missing_prices = [row["Ticker"] for _, row in changes.iterrows()
                                              if not (final_prices.get(row["Ticker"]) and final_prices[row["Ticker"]] > 0)]
                            st.warning(f"Enter prices for: {', '.join(missing_prices)} before applying.")

            except Exception as e:
                st.error(f"Error reading CSV: {e}")
                import traceback
                st.code(traceback.format_exc())

    # ── Holdings Table ──────────────────────────────────────────────────────
    holdings = db.get_holdings(sc_id)
    if holdings.empty:
        st.info("No stocks added yet. Use the form above or upload a CSV to add holdings.")
        return

    table = build_holdings_table(holdings, total_amount, is_design)
    if table.empty:
        st.warning("Could not build table. Check your data.")
        return

    # Summary metrics
    total_inv = table["Invested Amount"].sum()
    total_mv = table["Market Value"].sum()
    unrealized_pl = table["P/L"].sum()
    realized_info = db.get_realized_pnl(sc_id)
    realized_pl = realized_info["total_realized"]
    total_pl = unrealized_pl + realized_pl
    total_pl_pct = round(total_pl / total_inv * 100, 2) if total_inv > 0 else 0
    total_wt = table["Weightage %"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Invested", format_inr(total_inv))
    with c2:
        metric_card("Market Value", format_inr(total_mv),
                     "profit" if total_mv >= total_inv else "loss")
    with c3:
        metric_card("Unrealized P/L", format_inr(unrealized_pl),
                     "profit" if unrealized_pl >= 0 else "loss")
    with c4:
        metric_card("Realized P/L", format_inr(realized_pl),
                     "profit" if realized_pl >= 0 else "loss")

    c5, c6, c7 = st.columns(3)
    with c5:
        metric_card("Total P/L", f"{format_inr(total_pl)} ({total_pl_pct}%)",
                     "profit" if total_pl >= 0 else "loss")
    with c6:
        metric_card("Stocks", str(len(table)))
    with c7:
        wt_class = "profit" if abs(total_wt - 100) < 1 else "loss"
        metric_card("Total Weightage", f"{total_wt:.1f}%", wt_class)

    st.markdown("---")

    # Main holdings table
    st.subheader("Holdings")
    display_cols = ["Scrip Name", "Ticker", "Weightage %", "Units",
                    "Buy Date", "Buy Price", "Current Price",
                    "Invested Amount", "Market Value", "P/L", "P/L %",
                    "Days Held", "XIRR %", "Today Chg", "% Chg", "Industry"]
    display_df = table[display_cols].copy()

    # Copy stop-loss columns from table into display_df
    display_df["Stop Loss"] = table["Stop Loss"].values
    display_df["🚨 SL Hit"] = table["🚨 SL Hit"].values
    display_df["_sl_triggered"] = table["_sl_triggered"].values

    # Build a TradingView URL with the scrip name embedded as a URL fragment.
    def _stock_link(row) -> str:
        clean = str(row["Ticker"]).replace(".NS", "").replace(".BO", "")
        if clean == db.RESIDUAL_TICKER:
            return f"https://www.tradingview.com/symbols/NSE-LIQUIDBEES/#~{row['Scrip Name']}"
        return f"https://www.tradingview.com/chart/?symbol=NSE%3A{clean}#~{row['Scrip Name']}"

    display_df["Stock"] = display_df.apply(_stock_link, axis=1)

    # Grab sl_flags before dropping the internal column
    sl_flags = display_df["_sl_triggered"].tolist()

    # Only show Stop Loss columns when at least one stock has one set
    has_sl = display_df["Stop Loss"].apply(lambda x: x != "").any()

    final_cols = ["Stock", "Weightage %", "Units", "Buy Date", "Buy Price",
                  "Current Price", "Stop Loss", "🚨 SL Hit",
                  "Invested Amount", "Market Value", "P/L",
                  "P/L %", "Days Held", "XIRR %", "Today Chg", "% Chg", "Industry"]
    if not has_sl:
        final_cols = [c for c in final_cols if c not in ("Stop Loss", "🚨 SL Hit")]

    display_df = display_df[[c for c in final_cols if c in display_df.columns]]

    def _highlight_sl(row):
        """Turn entire row red if stop loss is triggered."""
        idx = row.name
        if idx < len(sl_flags) and sl_flags[idx]:
            return ["background-color: rgba(255,50,50,0.25); color: #ff8080"] * len(row)
        return [""] * len(row)

    fmt = {
        "Weightage %": "{:.1f}%",
        "Units": "{:.2f}",
        "Buy Price": "₹{:,.2f}",
        "Current Price": "₹{:,.2f}",
        "Invested Amount": "₹{:,.0f}",
        "Market Value": "₹{:,.0f}",
        "P/L": "₹{:,.0f}",
        "P/L %": "{:.2f}%",
        "Today Chg": "₹{:,.2f}",
        "% Chg": "{:.2f}%",
    }
    if has_sl:
        fmt["Stop Loss"] = lambda x: f"₹{x:,.2f}" if isinstance(x, (int, float)) and x > 0 else ""

    st.dataframe(
        display_df.style
            .apply(_highlight_sl, axis=1)
            .map(color_pnl, subset=["P/L", "P/L %", "Today Chg", "% Chg"])
            .format(fmt),
        width="stretch", hide_index=True,
        height=min(400, 50 + 35 * len(display_df)),
        column_config={
            "Stock": st.column_config.LinkColumn(
                "Stock 📈",
                help="Click the stock name to open its chart on TradingView",
                display_text=r"#~(.+)$",
                width="medium",
            ),
        },
    )

    # ── Edit / Delete / Exit Actions ────────────────────────────────────────
    st.subheader("Manage Holdings")
    tab_edit, tab_add_more, tab_reduce, tab_exit, tab_delete = st.tabs(
        ["✏️ Edit", "➕ Add More (Average)", "📉 Reduce Position", "🚪 Exit Position", "🗑️ Delete"]
    )

    stock_options = {f"{r['Scrip Name']} ({r['Ticker']})": r["ID"] for _, r in table.iterrows()}

    # Helper to show current stock summary
    def _stock_summary(h_id):
        row = table[table["ID"] == h_id].iloc[0]
        # Get stop_loss from the raw holdings df (not display table)
        raw_row = holdings[holdings["id"] == h_id]
        sl = float(raw_row["stop_loss"].iloc[0]) if not raw_row.empty and "stop_loss" in raw_row.columns else 0.0
        return row, {
            "wt": float(row["Weightage %"]),
            "bp": float(row["Buy Price"]),
            "ind": str(row["Industry"]),
            "units": float(row["Units"]),
            "inv": float(row["Invested Amount"]),
            "sl": sl,
        }

    with tab_edit:
        if stock_options:
            sel = st.selectbox("Select stock to edit", list(stock_options.keys()), key=f"edit_sel_{sc_id}")
            h_id = stock_options[sel]
            sel_row, cur = _stock_summary(h_id)

            st.caption(
                f"Current: Weightage **{cur['wt']}%** · Buy Price **₹{cur['bp']:,.2f}** · "
                f"Units **{cur['units']:.2f}** · Invested **₹{cur['inv']:,.2f}** · "
                f"Industry **{cur['ind']}**"
            )

            with st.form(f"edit_form_{sc_id}_{h_id}"):
                st.markdown("*Direct replacement — changes overwrite existing values.*")
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_wt = st.number_input("Weightage %", 0.0, 100.0, value=cur["wt"], step=0.5,
                                             key=f"ewt_{sc_id}_{h_id}")
                    new_bp = st.number_input("Buy Price (₹)", 0.0, value=cur["bp"], step=0.5,
                                             key=f"ebp_{sc_id}_{h_id}")
                    new_sl = st.number_input("Stop Loss (₹) — 0 to remove",
                                             min_value=0.0, value=cur["sl"], step=0.5,
                                             key=f"esl_{sc_id}_{h_id}",
                                             help="Row turns red when current price ≤ this value. Set 0 to disable.")
                with ec2:
                    new_ind = st.text_input("Industry", value=cur["ind"], key=f"eind_{sc_id}_{h_id}")
                    new_units = st.number_input("Units", 0.0, value=cur["units"], step=1.0,
                                                key=f"eunits_{sc_id}_{h_id}")

                recalc_units = st.checkbox("Recalculate units from weightage",
                                           value=False, key=f"erecalc_{sc_id}_{h_id}",
                                           help="Units = (Weightage% × Investable Amount) / Buy Price")

                # Show LIQUIDCASE exit price if editing a non-LIQUIDCASE stock's weightage
                liq_ep_edit = 0.0
                if sel_row["Ticker"] != db.RESIDUAL_TICKER:
                    liq_ep_edit = st.number_input(
                        "LIQUIDCASE exit price (₹) — for auto-rebalance",
                        min_value=0.0, step=0.1, value=0.0,
                        key=f"eliq_{sc_id}_{h_id}",
                        help="Price at which LIQUIDCASE units are sold/bought. Leave 0 to use buy price."
                    )

                if st.form_submit_button("Update"):
                    updates = {}
                    if new_wt != cur["wt"]:
                        updates["weightage"] = new_wt
                    if new_bp != cur["bp"]:
                        updates["buy_price"] = new_bp
                    if new_ind != cur["ind"]:
                        updates["industry"] = new_ind
                    if new_sl != cur["sl"]:
                        updates["stop_loss"] = new_sl

                    if recalc_units:
                        bp = new_bp if new_bp > 0 else cur["bp"]
                        updates["units"] = fin.calculate_units(new_wt, total_amount, bp)
                    elif new_units != cur["units"]:
                        updates["units"] = new_units

                    if updates:
                        db.update_holding(h_id, **updates)

                        # Auto-rebalance LIQUIDCASE if weightage changed on a non-LIQUIDCASE stock
                        if "weightage" in updates and sel_row["Ticker"] != db.RESIDUAL_TICKER:
                            rb = db.rebalance_residual(sc_id, total_amount,
                                                       exit_price=liq_ep_edit if liq_ep_edit > 0 else None)
                            if rb:
                                st.info(f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                        f"({rb['delta_units']:+.2f} units)")

                        st.success("Updated!")
                        st.rerun()
                    else:
                        st.info("No changes detected.")

    with tab_add_more:
        st.markdown("**Add more quantity to an existing position (average up/down)**")
        st.markdown(
            "> Pick a date → opening price is auto-fetched. "
            "The system calculates new total units and weighted average buy price."
        )
        if stock_options:
            sel_avg = st.selectbox("Select stock to add more", list(stock_options.keys()),
                                   key=f"avg_sel_{sc_id}")
            h_id_avg = stock_options[sel_avg]
            sel_row_avg, cur_avg = _stock_summary(h_id_avg)
            avg_ticker = sel_row_avg["Ticker"]

            st.caption(
                f"Current: Weightage **{cur_avg['wt']}%** · "
                f"Avg Buy Price **₹{cur_avg['bp']:,.2f}** · "
                f"Units **{cur_avg['units']:.2f}** · "
                f"Invested **₹{cur_avg['inv']:,.2f}**"
            )

            # Date picker OUTSIDE form — triggers auto-fetch
            avg_date = st.date_input("Date of Buy (open price auto-fetched)",
                                      value=date.today(), key=f"adate_{sc_id}")
            avg_date_str = avg_date.strftime("%Y-%m-%d")

            # Auto-fetch opening price for the selected date
            fetched_avg_price = fin.fetch_open_price(avg_ticker, avg_date_str) or 0.0
            if fetched_avg_price > 0:
                st.success(f"📈 Opening price of **{avg_ticker}** on **{avg_date_str}**: **₹{fetched_avg_price:,.2f}**")
            else:
                st.warning(f"Could not fetch price for {avg_ticker} on {avg_date_str}. Enter manually below.")

            # Also fetch LIQUIDCASE price for same date
            liq_price_avg = fin.fetch_open_price(db.RESIDUAL_TICKER, avg_date_str) or 0.0

            with st.form(f"avg_form_{sc_id}_{h_id_avg}"):
                ac1, ac2 = st.columns(2)
                with ac1:
                    add_wt = st.number_input(
                        "Additional Weightage %", 0.0, 100.0, value=0.0, step=0.5,
                        key=f"awt_{sc_id}_{h_id_avg}",
                        help="Extra weightage to add (e.g., 3% on top of existing 7%)"
                    )
                with ac2:
                    add_bp = st.number_input(
                        "Buy Price for new tranche (₹)", 0.0, step=0.5,
                        value=float(fetched_avg_price),
                        key=f"abp_{sc_id}_{h_id_avg}_{avg_date_str}",
                        help="Auto-filled with opening price. Override if needed."
                    )

                # Preview
                if add_wt > 0 and add_bp > 0:
                    add_units = round((add_wt / 100 * total_amount) / add_bp, 4)
                    new_total_units = cur_avg["units"] + add_units
                    new_total_wt = cur_avg["wt"] + add_wt
                    old_cost = cur_avg["units"] * cur_avg["bp"]
                    new_cost = add_units * add_bp
                    new_avg_price = round((old_cost + new_cost) / new_total_units, 2) if new_total_units > 0 else 0

                    st.markdown("---")
                    st.markdown("**Preview after averaging:**")
                    pc1, pc2, pc3, pc4 = st.columns(4)
                    pc1.metric("New Weightage", f"{new_total_wt:.1f}%", f"+{add_wt:.1f}%")
                    pc2.metric("New Units", f"{new_total_units:.2f}", f"+{add_units:.2f}")
                    pc3.metric("Avg Buy Price", f"₹{new_avg_price:,.2f}",
                               f"{'↑' if new_avg_price > cur_avg['bp'] else '↓'} from ₹{cur_avg['bp']:,.2f}")
                    pc4.metric("Total Invested", f"₹{old_cost + new_cost:,.2f}",
                               f"+₹{new_cost:,.2f}")

                # LIQUIDCASE exit price for rebalancing
                liq_ep_avg = 0.0
                if sel_row_avg["Ticker"] != db.RESIDUAL_TICKER:
                    liq_ep_avg = st.number_input(
                        "LIQUIDCASE exit price (₹) — auto-fetched",
                        min_value=0.0, step=0.1,
                        value=float(liq_price_avg),
                        key=f"aliq_{sc_id}_{h_id_avg}_{avg_date_str}",
                        help="Auto-filled with LIQUIDCASE opening price on same date. Override if needed."
                    )

                if st.form_submit_button("Add & Average"):
                    if add_wt <= 0 or add_bp <= 0:
                        st.error("Please enter both additional weightage and buy price.")
                    else:
                        add_units = round((add_wt / 100 * total_amount) / add_bp, 4)
                        new_total_units = cur_avg["units"] + add_units
                        new_total_wt = cur_avg["wt"] + add_wt
                        old_cost = cur_avg["units"] * cur_avg["bp"]
                        new_cost = add_units * add_bp
                        new_avg_price = round((old_cost + new_cost) / new_total_units, 2)

                        db.update_holding(h_id_avg,
                                          weightage=new_total_wt,
                                          units=new_total_units,
                                          buy_price=new_avg_price)

                        # Log the BUY transaction
                        conn = db.get_connection()
                        conn.execute(
                            "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
                            "VALUES (?, ?, ?, 'BUY', ?, ?, ?)",
                            (h_id_avg, sc_id, avg_ticker, add_units, add_bp, avg_date_str)
                        )
                        conn.commit()
                        conn.close()

                        # Auto-rebalance LIQUIDCASE
                        if sel_row_avg["Ticker"] != db.RESIDUAL_TICKER:
                            rb = db.rebalance_residual(sc_id, total_amount,
                                                       exit_price=liq_ep_avg if liq_ep_avg > 0 else None)
                            if rb:
                                st.info(f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                        f"({rb['delta_units']:+.2f} units)")

                        st.success(
                            f"Averaged! New: {new_total_wt:.1f}% · "
                            f"{new_total_units:.2f} units · "
                            f"Avg Price ₹{new_avg_price:,.2f}"
                        )
                        st.rerun()

    with tab_reduce:
        st.markdown("**Reduce weightage of a stock (partial sell)**")
        st.markdown(
            "> Pick a date → opening price is auto-fetched as exit price. "
            "The freed weightage automatically flows back to LIQUIDCASE."
        )
        if stock_options:
            # Filter out LIQUIDCASE from reduce options
            reduce_options = {k: v for k, v in stock_options.items()
                              if not k.endswith(f"({db.RESIDUAL_TICKER})")}

            if reduce_options:
                sel_red = st.selectbox("Select stock to reduce", list(reduce_options.keys()),
                                       key=f"red_sel_{sc_id}")
                h_id_red = reduce_options[sel_red]
                sel_row_red, cur_red = _stock_summary(h_id_red)
                red_ticker = sel_row_red["Ticker"]

                st.caption(
                    f"Current: Weightage **{cur_red['wt']}%** · "
                    f"Avg Buy Price **₹{cur_red['bp']:,.2f}** · "
                    f"Units **{cur_red['units']:.2f}** · "
                    f"Invested **₹{cur_red['inv']:,.2f}**"
                )

                # Date picker OUTSIDE form — triggers auto-fetch
                red_date = st.date_input("Date of Reduction (open price auto-fetched)",
                                          value=date.today(), key=f"rdt_{sc_id}")
                red_date_str = red_date.strftime("%Y-%m-%d")

                # Auto-fetch opening price
                fetched_red_price = fin.fetch_open_price(red_ticker, red_date_str) or 0.0
                if fetched_red_price > 0:
                    st.success(f"📉 Opening price of **{red_ticker}** on **{red_date_str}**: **₹{fetched_red_price:,.2f}**")
                else:
                    st.warning(f"Could not fetch price for {red_ticker} on {red_date_str}. Enter manually below.")

                # Also fetch LIQUIDCASE price for same date
                liq_price_red = fin.fetch_open_price(db.RESIDUAL_TICKER, red_date_str) or 0.0

                with st.form(f"reduce_form_{sc_id}_{h_id_red}"):
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        new_wt_red = st.number_input(
                            "New Weightage %", 0.0, cur_red["wt"],
                            value=cur_red["wt"], step=0.5,
                            key=f"rwt_{sc_id}_{h_id_red}",
                            help=f"Current: {cur_red['wt']}%. Set lower to reduce."
                        )
                    with rc2:
                        red_exit_price = st.number_input(
                            "Exit Price for sold units (₹)", 0.0, step=0.5,
                            value=float(fetched_red_price),
                            key=f"rep_{sc_id}_{h_id_red}_{red_date_str}",
                            help="Auto-filled with opening price. Override if needed."
                        )

                    # Preview
                    wt_diff = cur_red["wt"] - new_wt_red
                    if wt_diff > 0 and red_exit_price > 0:
                        # New units based on new weightage
                        new_units_red = round((new_wt_red / 100 * total_amount) / cur_red["bp"], 4) if cur_red["bp"] > 0 else 0
                        sold_units = round(cur_red["units"] - new_units_red, 4)
                        sell_value = round(sold_units * red_exit_price, 2)

                        st.markdown("---")
                        st.markdown("**Preview after reduction:**")
                        pc1, pc2, pc3, pc4 = st.columns(4)
                        pc1.metric("New Weightage", f"{new_wt_red:.1f}%", f"-{wt_diff:.1f}%", delta_color="inverse")
                        pc2.metric("Remaining Units", f"{new_units_red:.2f}", f"-{sold_units:.2f}", delta_color="inverse")
                        pc3.metric("Units Sold", f"{sold_units:.2f}", f"@ ₹{red_exit_price:,.2f}")
                        pc4.metric("Sale Value", f"₹{sell_value:,.2f}")

                    if st.form_submit_button("Reduce & Rebalance"):
                        if new_wt_red >= cur_red["wt"]:
                            st.error("New weightage must be lower than current. Use 'Add More' to increase.")
                        elif red_exit_price <= 0:
                            st.error("Please enter the exit price for sold units.")
                        else:
                            # Calculate new units based on reduced weightage
                            new_units_red = round((new_wt_red / 100 * total_amount) / cur_red["bp"], 4) if cur_red["bp"] > 0 else 0
                            sold_units = round(cur_red["units"] - new_units_red, 4)

                            # Update the holding
                            db.update_holding(h_id_red,
                                              weightage=new_wt_red,
                                              units=new_units_red)

                            # Log the partial SELL transaction
                            conn = db.get_connection()
                            conn.execute(
                                "INSERT INTO transactions (holding_id, smallcase_id, ticker, action, units, price, transaction_date) "
                                "VALUES (?, ?, ?, 'SELL', ?, ?, ?)",
                                (h_id_red, sc_id, red_ticker, sold_units,
                                 red_exit_price, red_date_str)
                            )
                            conn.commit()
                            conn.close()

                            # Auto-rebalance LIQUIDCASE (freed weightage flows back)
                            rb = db.rebalance_residual(sc_id, total_amount,
                                                       exit_price=liq_price_red if liq_price_red > 0 else None)
                            if rb:
                                st.info(
                                    f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                    f"({rb['delta_units']:+.2f} units)"
                                )

                            st.success(
                                f"Reduced {red_ticker}: "
                                f"{cur_red['wt']:.1f}% → {new_wt_red:.1f}% · "
                                f"Sold {sold_units:.2f} units @ ₹{red_exit_price:,.2f}"
                            )
                            st.rerun()
            else:
                st.info("No stocks to reduce (only LIQUIDCASE in portfolio).")

    with tab_exit:
        if stock_options:
            sel_exit = st.selectbox("Select stock to exit", list(stock_options.keys()), key=f"exit_sel_{sc_id}")
            h_id_exit = stock_options[sel_exit]
            exit_row = table[table["ID"] == h_id_exit].iloc[0]
            exit_ticker = exit_row["Ticker"]

            # Date picker OUTSIDE form — triggers auto-fetch
            exit_date = st.date_input("Exit Date (open price auto-fetched)",
                                       value=date.today(), key=f"exd_{sc_id}")
            exit_date_str = exit_date.strftime("%Y-%m-%d")

            fetched_exit_price = fin.fetch_open_price(exit_ticker, exit_date_str) or 0.0
            if fetched_exit_price > 0:
                st.success(f"📉 Opening price of **{exit_ticker}** on **{exit_date_str}**: **₹{fetched_exit_price:,.2f}**")
            else:
                st.warning(f"Could not fetch price for {exit_ticker} on {exit_date_str}. Enter manually below.")

            with st.form(f"exit_form_{sc_id}_{exit_date_str}"):
                exit_price = st.number_input("Exit Price (₹)", 0.0,
                                              value=float(fetched_exit_price),
                                              key=f"exp_{sc_id}_{h_id_exit}_{exit_date_str}",
                                              help="Auto-filled with opening price. Override if needed.")
                if st.form_submit_button("Exit Position"):
                    if exit_price <= 0:
                        st.error("Please enter a valid exit price.")
                    else:
                        db.exit_holding(h_id_exit, exit_price, exit_date_str)
                        # Auto-rebalance LIQUIDCASE (freed weightage goes back)
                        if exit_ticker != db.RESIDUAL_TICKER:
                            liq_price_exit = fin.fetch_open_price(db.RESIDUAL_TICKER, exit_date_str) or 0.0
                            rb = db.rebalance_residual(sc_id, total_amount,
                                                       exit_price=liq_price_exit if liq_price_exit > 0 else None)
                            if rb:
                                st.info(f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                        f"({rb['delta_units']:+.2f} units)")
                        st.success("Position exited!")
                        st.rerun()

    with tab_delete:
        if stock_options:
            sel_del = st.selectbox("Select stock to delete", list(stock_options.keys()), key=f"del_sel_{sc_id}")
            h_id_del = stock_options[sel_del]
            del_row = table[table["ID"] == h_id_del].iloc[0]
            if st.button("Confirm Delete", key=f"delbtn_{sc_id}"):
                db.delete_holding(h_id_del)
                # Auto-rebalance LIQUIDCASE (freed weightage goes back)
                if del_row["Ticker"] != db.RESIDUAL_TICKER:
                    rb = db.rebalance_residual(sc_id, total_amount)
                    if rb:
                        st.info(f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                f"({rb['delta_units']:+.2f} units)")
                st.success("Deleted!")
                st.rerun()

    st.markdown("---")

    # ── Analytics ───────────────────────────────────────────────────────────
    analytics_open = st.expander("Analytics & Risk Metrics", expanded=False)
    with analytics_open:
        # Fetch stock info for beta, div yield — cached, only runs when expanded
        tickers = table["Ticker"].tolist()
        weightages = table["Weightage %"].tolist()

        infos = fin.fetch_stock_info_batch(tickers)

        betas = [infos[t]["beta"] for t in tickers]
        div_yields = [infos[t]["dividend_yield"] for t in tickers]
        industries = [infos[t]["industry"] if infos[t]["industry"] else table.loc[table["Ticker"] == t, "Industry"].iloc[0] for t in tickers]

        w_beta = fin.calculate_weighted_beta(betas, weightages)
        w_div = fin.calculate_weighted_div_yield(div_yields, weightages)
        sector_conc = fin.get_sector_concentration(industries, weightages)

        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            metric_card("Weighted Avg Beta", f"{w_beta:.3f}" if w_beta else "N/A")
        with ac2:
            metric_card("Weighted Div Yield", f"{w_div:.2f}%")
        with ac3:
            vol = fin.calculate_portfolio_volatility(tickers, weightages)
            metric_card("Portfolio Volatility (1Y)", f"{vol:.2f}%" if vol else "N/A")

        # Sector concentration
        st.subheader("Sector Concentration")
        col_sc1, col_sc2 = st.columns([2, 3])

        with col_sc1:
            for sector, wt in sector_conc.items():
                bar_color = "🔴" if wt > 30 else "🟢"
                st.markdown(f"{bar_color} **{sector}**: {wt:.1f}%")
                if wt > 30:
                    st.markdown(f'<div class="flag-warning">⚠️ Concentration Warning: {sector} is {wt:.1f}% (>30%)</div>',
                                unsafe_allow_html=True)

        with col_sc2:
            if sector_conc:
                fig = px.bar(
                    x=list(sector_conc.values()),
                    y=list(sector_conc.keys()),
                    orientation="h",
                    color=list(sector_conc.values()),
                    color_continuous_scale=["#26a69a", "#ffca28", "#ff5252"],
                    labels={"x": "Weightage %", "y": "Sector"},
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0",
                    height=300,
                    margin=dict(t=10, b=10),
                    showlegend=False,
                    coloraxis_showscale=False,
                    xaxis=dict(showgrid=True, gridcolor="#2d2d44"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig, width="stretch")

    # P/L Heatmap — always visible outside expander
    st.subheader("P/L Heatmap")
    if not table.empty:
        tree_df = table[["Scrip Name", "Industry", "Market Value", "P/L %"]].copy()
        tree_df["abs_mv"] = tree_df["Market Value"].abs().clip(lower=1)
        fig = px.treemap(
            tree_df,
            path=["Industry", "Scrip Name"],
            values="abs_mv",
            color="P/L %",
            color_continuous_scale=["#ff5252", "#ffca28", "#00e676"],
            color_continuous_midpoint=0,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            height=400,
            margin=dict(t=30, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, width="stretch")

    # Realized P/L — closed positions
    if realized_info["details"]:
        st.subheader("Realized P/L · Closed Positions")
        rp_rows = []
        for d in realized_info["details"]:
            rp_rows.append({
                "Scrip Name": d["scrip_name"],
                "Ticker": d["ticker"],
                "Units": round(d["units"], 2),
                "Buy Date": d["buy_date"] or "",
                "Buy Price": d["buy_price"],
                "Exit Date": d["exit_date"] or "",
                "Exit Price": d["exit_price"],
                "Cost": d["cost"],
                "Proceeds": d["proceeds"],
                "Realized P/L": d["pnl"],
                "P/L %": round(d["pnl_pct"], 2),
            })
        rp_df = pd.DataFrame(rp_rows)
        st.dataframe(
            rp_df.style
                .map(color_pnl, subset=["Realized P/L", "P/L %"])
                .format({
                    "Units": "{:.2f}",
                    "Buy Price": "₹{:,.2f}",
                    "Exit Price": "₹{:,.2f}",
                    "Cost": "₹{:,.0f}",
                    "Proceeds": "₹{:,.0f}",
                    "Realized P/L": "₹{:,.0f}",
                    "P/L %": "{:.2f}%",
                }),
            width="stretch", hide_index=True,
        )

    # Transaction log
    st.subheader("Transaction Log")
    txns = db.get_transactions(sc_id)
    if not txns.empty:
        st.dataframe(
            txns[["transaction_date", "ticker", "action", "units", "price"]].rename(columns={
                "transaction_date": "Date", "ticker": "Ticker", "action": "Action",
                "units": "Units", "price": "Price",
            }),
            width="stretch", hide_index=True,
        )
    else:
        st.info("No transactions recorded yet.")


# ── Router ──────────────────────────────────────────────────────────────────

if nav == "🏠 Master Dashboard":
    render_master_dashboard()
else:
    # Find the matching smallcase
    for sc in all_sc:
        label = f"{'🧪' if sc['is_design_mode'] else '📁'} {sc['name']}"
        if nav == label:
            render_smallcase(sc)
            break
