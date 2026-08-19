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
import io
import database as db
import finance as fin

# ── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Smallcase Dashboard",
    page_icon="🙏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Database connectivity guard ─────────────────────────────────────────────
# If the database could not be reached at startup, show the real error clearly
# instead of letting the app crash to a blank "Oh no" page.
if getattr(db, "INIT_ERROR", None):
    st.error("🚨 Cannot connect to the database.")
    st.markdown(
        "The app started, but it could not reach your Neon PostgreSQL database. "
        "Your data is safe in Neon — this is only a connection problem.\n\n"
        "**Most likely fix:** the `DATABASE_URL` in **Streamlit → Settings → Secrets** "
        "doesn't match your current Neon database. Copy the **pooled** connection string "
        "from Neon's **Connect** dialog and paste it into the Streamlit secret."
    )
    st.markdown("**Exact error from the database driver:**")
    st.code(db.INIT_ERROR, language="text")
    st.stop()

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

    /* ── Sidebar navigation: compact, left-aligned, single-line ── */
    div[data-testid="stSidebar"] .stButton > button {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        color: #cfd8e3;
        font-size: 13.5px;
        font-weight: 500;
        line-height: 1.25;
        padding: 6px 10px;
        min-height: 0;
        height: auto;
        margin: 1px 0;
        text-align: left;
        justify-content: flex-start;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: background .12s ease, border-color .12s ease;
    }
    /* The label lives in a <p> inside the button; it needs its own overflow
       rules (and min-width:0 to be allowed to shrink inside the flex button)
       or long folio names clip mid-word with no ellipsis. */
    div[data-testid="stSidebar"] .stButton > button p {
        display: block;
        width: 100%;
        min-width: 0;
        max-width: 100%;
        text-align: left;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 13.5px;
        line-height: 1.3;
        margin: 0;
    }
    div[data-testid="stSidebar"] .stButton > button > div {
        width: 100%;
        min-width: 0;
        justify-content: flex-start;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(212, 175, 55, 0.09);
        border-color: rgba(212, 175, 55, 0.28);
        color: #f0d060;
    }
    /* Active item — gold left rail.
       Streamlit's own primary-button styles are highly specific (emotion
       classes), so these need !important to win. */
    div[data-testid="stSidebar"] .stButton > button[kind="primary"],
    div[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
        background: rgba(212, 175, 55, 0.14) !important;
        background-color: rgba(212, 175, 55, 0.14) !important;
        background-image: none !important;
        border: 1px solid rgba(212, 175, 55, 0.40) !important;
        border-left: 3px solid #d4af37 !important;
        color: #f5e6a8 !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] .stButton > button[kind="primary"] p,
    div[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] p {
        color: #f5e6a8 !important;
    }
    div[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
    div[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: rgba(212, 175, 55, 0.22) !important;
        background-color: rgba(212, 175, 55, 0.22) !important;
        border-color: rgba(212, 175, 55, 0.55) !important;
        color: #ffe9a8 !important;
    }

    /* Group expander headers */
    div[data-testid="stSidebar"] details {
        border: none !important;
        background: transparent !important;
        margin-bottom: 2px;
    }
    div[data-testid="stSidebar"] summary {
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 1.1px;
        text-transform: uppercase;
        color: #8a97a8 !important;
        padding: 4px 6px !important;
    }
    div[data-testid="stSidebar"] summary:hover { color: #d4af37 !important; }
    /* Tighten the vertical rhythm of stacked nav items */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.15rem; }

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


# ── Insight strip ───────────────────────────────────────────────────────────

def _insight_card(title: str, headline: str, sub: str, tone: str = "neutral"):
    """Small card used by the insight strip. `tone` drives the accent colour."""
    accent = {"profit": "#00e676", "loss": "#ff5252",
              "warn": "#ffca28", "neutral": "#8899a6"}.get(tone, "#8899a6")
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
                border-left:3px solid {accent}; border-radius:8px;
                padding:10px 14px; height:100%;">
      <div style="font-size:10px; letter-spacing:1.4px; text-transform:uppercase;
                  color:#8899a6; margin-bottom:4px;">{title}</div>
      <div style="font-size:15px; font-weight:600; color:{accent}; line-height:1.3;">{headline}</div>
      <div style="font-size:11px; color:#aab8c2; margin-top:2px;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def render_insight_strip(table: pd.DataFrame):
    """At-a-glance callouts above the holdings table: today's movers, best/worst
    holding, and anything that needs attention (stop losses, concentration)."""
    if table.empty:
        return

    live = table[table["% Chg"] != 0]
    priced = table[table["Invested Amount"] > 0]

    c1, c2, c3, c4 = st.columns(4)

    # Today's biggest mover (up)
    with c1:
        if not live.empty:
            top = live.loc[live["% Chg"].idxmax()]
            tone = "profit" if top["% Chg"] > 0 else "loss"
            _insight_card("Today's Top Gainer",
                          f"{top['Scrip Name'][:22]}  {top['% Chg']:+.2f}%",
                          f"₹{top['Today Chg']:+,.2f} per share", tone)
        else:
            _insight_card("Today's Top Gainer", "—", "Live prices unavailable")

    # Today's biggest mover (down)
    with c2:
        if not live.empty:
            bot = live.loc[live["% Chg"].idxmin()]
            tone = "loss" if bot["% Chg"] < 0 else "profit"
            _insight_card("Today's Top Loser",
                          f"{bot['Scrip Name'][:22]}  {bot['% Chg']:+.2f}%",
                          f"₹{bot['Today Chg']:+,.2f} per share", tone)
        else:
            _insight_card("Today's Top Loser", "—", "Live prices unavailable")

    # Best holding by P/L %
    with c3:
        if not priced.empty:
            best = priced.loc[priced["P/L %"].idxmax()]
            _insight_card("Best Holding",
                          f"{best['Scrip Name'][:22]}  {best['P/L %']:+.1f}%",
                          f"{format_inr(best['P/L'])} gain",
                          "profit" if best["P/L"] >= 0 else "loss")
        else:
            _insight_card("Best Holding", "—", "No priced holdings")

    # Needs attention: SL hits, then concentration, else worst drag
    with c4:
        sl_hits = table[table["_sl_triggered"]] if "_sl_triggered" in table.columns else pd.DataFrame()
        heavy = table[table["Weightage %"] > 15]
        if not sl_hits.empty:
            names = ", ".join(sl_hits["Scrip Name"].head(2).tolist())
            _insight_card("Needs Attention",
                          f"🚨 {len(sl_hits)} stop-loss hit",
                          names[:44], "loss")
        elif not heavy.empty:
            h = heavy.loc[heavy["Weightage %"].idxmax()]
            _insight_card("Needs Attention",
                          f"⚠️ {h['Scrip Name'][:18]} is {h['Weightage %']:.1f}%",
                          f"{len(heavy)} position(s) above 15%", "warn")
        elif not priced.empty:
            worst = priced.loc[priced["P/L"].idxmin()]
            if worst["P/L"] < 0:
                _insight_card("Biggest Drag",
                              f"{worst['Scrip Name'][:22]}  {worst['P/L %']:+.1f}%",
                              f"{format_inr(worst['P/L'])}", "loss")
            else:
                _insight_card("Needs Attention", "✅ All clear",
                              "No stop-loss or concentration flags", "profit")
        else:
            _insight_card("Needs Attention", "—", "")


# ── Portfolio charts ────────────────────────────────────────────────────────

_CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e0e0e0", margin=dict(t=30, b=30, l=10, r=10),
)


def render_portfolio_charts(table: pd.DataFrame):
    """P/L contribution by stock + allocation treemap."""
    if table.empty:
        return

    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("**P/L Contribution by Stock**")
        d = table[["Scrip Name", "P/L"]].copy()
        d = d[d["P/L"] != 0].sort_values("P/L")
        if d.empty:
            st.caption("No profit/loss to show yet.")
        else:
            fig = go.Figure(go.Bar(
                x=d["P/L"], y=d["Scrip Name"], orientation="h",
                marker_color=["#ff5252" if v < 0 else "#00e676" for v in d["P/L"]],
                hovertemplate="%{y}<br>₹%{x:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                **_CHART_LAYOUT,
                height=max(260, 26 * len(d)),
                xaxis=dict(title="P/L (₹)", showgrid=True, gridcolor="#2d2d44",
                           zerolinecolor="#4a4a6a"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown("**Allocation** — size = market value, colour = return")
        d = table[table["Market Value"] > 0][
            ["Scrip Name", "Market Value", "P/L %", "P/L"]].copy()
        if d.empty:
            st.caption("No holdings to show yet.")
        else:
            fig = px.treemap(
                d, path=["Scrip Name"], values="Market Value",
                color="P/L %", color_continuous_scale=["#ff5252", "#37474f", "#00e676"],
                color_continuous_midpoint=0,
                custom_data=["P/L %", "P/L"],
            )
            fig.update_traces(
                texttemplate="%{label}<br>%{customdata[0]:+.1f}%",
                hovertemplate="%{label}<br>Value ₹%{value:,.0f}"
                              "<br>Return %{customdata[0]:+.2f}%"
                              "<br>P/L ₹%{customdata[1]:,.0f}<extra></extra>",
            )
            fig.update_layout(**_CHART_LAYOUT, height=max(260, 26 * len(d)),
                              coloraxis_colorbar=dict(title="Return %"))
            st.plotly_chart(fig, use_container_width=True)


# ── Excel export ────────────────────────────────────────────────────────────

EXPORT_COLS = ["Scrip Name", "Ticker", "Weightage %", "Units", "Buy Date",
               "Buy Price", "Current Price", "Invested Amount", "Market Value",
               "P/L", "P/L %", "Days Held", "XIRR %"]


def build_portfolio_excel(table: pd.DataFrame, sc_name: str,
                          summary: dict) -> bytes | None:
    """Formatted single-sheet Excel statement. Returns None if openpyxl absent."""
    try:
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except Exception:
        return None

    cols = [c for c in EXPORT_COLS if c in table.columns]
    df = table[cols].copy()

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Table starts below a title + summary block
        start_row = len(summary) + 4
        df.to_excel(writer, index=False, sheet_name="Portfolio", startrow=start_row)
        ws = writer.sheets["Portfolio"]

        gold = Font(bold=True, size=14, color="B8860B")
        ws.cell(row=1, column=1, value=f"{sc_name} — Portfolio Statement").font = gold
        ws.cell(row=2, column=1,
                value=f"As on {datetime.now().strftime('%d %b %Y, %I:%M %p')}").font = \
            Font(size=9, italic=True, color="808080")

        # Summary block
        for i, (k, v) in enumerate(summary.items()):
            r = 4 + i
            ws.cell(row=r, column=1, value=k).font = Font(bold=True)
            ws.cell(row=r, column=2, value=v)

        # Header row styling
        hdr_row = start_row + 1
        head_fill = PatternFill("solid", fgColor="1F3864")
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=hdr_row, column=c)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = head_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Number formats + red/green P/L
        money = '#,##0.00'
        pct = '0.00"%"'
        fmt_map = {"Buy Price": money, "Current Price": money,
                   "Invested Amount": money, "Market Value": money, "P/L": money,
                   "Weightage %": pct, "P/L %": pct, "XIRR %": pct, "Units": '#,##0.00'}
        for ci, name in enumerate(cols, start=1):
            if name in fmt_map:
                for r in range(hdr_row + 1, hdr_row + 1 + len(df)):
                    ws.cell(row=r, column=ci).number_format = fmt_map[name]
            if name in ("P/L", "P/L %", "XIRR %"):
                for r in range(hdr_row + 1, hdr_row + 1 + len(df)):
                    cell = ws.cell(row=r, column=ci)
                    if isinstance(cell.value, (int, float)):
                        cell.font = Font(color="008000" if cell.value >= 0 else "CC0000")

        # Totals row
        tot_row = hdr_row + len(df) + 1
        ws.cell(row=tot_row, column=1, value="TOTAL").font = Font(bold=True)
        for ci, name in enumerate(cols, start=1):
            if name in ("Invested Amount", "Market Value", "P/L"):
                col = get_column_letter(ci)
                cell = ws.cell(row=tot_row, column=ci)
                cell.value = f"=SUM({col}{hdr_row+1}:{col}{hdr_row+len(df)})"
                cell.font = Font(bold=True)
                cell.number_format = money

        # Column widths + frozen header
        for ci, name in enumerate(cols, start=1):
            longest = max([len(str(name))] +
                          [len(str(v)) for v in df[name].head(60).tolist()])
            ws.column_dimensions[get_column_letter(ci)].width = min(max(longest + 2, 11), 34)
        ws.freeze_panes = ws.cell(row=hdr_row + 1, column=1)

    buf.seek(0)
    return buf.getvalue()


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
        sc_group = st.text_input("Group (e.g. Smallcase / App / R Wadiwala)",
                                  help="Group multiple folios together on the Master Dashboard")
        sc_amount = st.number_input("Total Investable Amount (₹)", min_value=0.0,
                                    value=100000.0, step=10000.0)
        sc_design = st.checkbox("Design Mode (Simulation)", value=False)
        submitted = st.form_submit_button("Create")
        if submitted and sc_name:
            try:
                db.create_smallcase(sc_name, sc_desc, sc_amount, sc_design)
                # Save group name immediately after creation
                new_sc_list = db.get_all_smallcases()
                for s in new_sc_list:
                    if s["name"] == sc_name:
                        db.update_smallcase(s["id"], group_name=sc_group.strip())
                        break
                st.success(f"Created: {sc_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# List all smallcases
all_sc = db.get_all_smallcases()
sc_names = [s["name"] for s in all_sc]

if not all_sc:
    st.sidebar.info("No smallcases yet. Create one above.")

# ── Grouped Sidebar Navigation ──────────────────────────────────────────────
st.sidebar.markdown("---")

# Session-state based navigation (replaces radio widget)
if "nav" not in st.session_state:
    st.session_state["nav"] = "🏠 Master Dashboard"

def _nav_btn(label: str, key: str, container=None, tooltip: str | None = None):
    """Render a nav button. Active item uses type='primary' so the CSS above
    can style it with a gold left rail."""
    target = container if container is not None else st.sidebar
    is_active = st.session_state["nav"] == label
    if target.button(
        label, key=key, use_container_width=True,
        type="primary" if is_active else "secondary",
        help=tooltip,
    ):
        st.session_state["nav"] = label
        st.rerun()


# Master Dashboard — always at top
_nav_btn("🏠 Master Dashboard", "nav_master")
# Mutual Funds — always visible as second item
_nav_btn("📊 Mutual Funds", "nav_mf")

# Group folios by group_name
_groups: dict[str, list] = {}
_ungrouped: list = []
for _sc in all_sc:
    _grp = (_sc.get("group_name") or "").strip()
    _label = f"{'🧪' if _sc['is_design_mode'] else '📁'} {_sc['name']}"
    if _grp:
        _groups.setdefault(_grp, []).append((_label, _sc))
    else:
        _ungrouped.append((_label, _sc))

# Render each group as a collapsible section, with a count badge so you can see
# how many folios a collapsed group holds without opening it.
for _grp_name, _folios in sorted(_groups.items()):
    _active_in_group = any(st.session_state["nav"] == lbl for lbl, _ in _folios)
    _hdr = f"{_grp_name}  ·  {len(_folios)}"
    with st.sidebar.expander(_hdr, expanded=_active_in_group):
        for _lbl, _sc in _folios:
            _nav_btn(_lbl, f"nav_{_sc['id']}", container=st,
                     tooltip=_sc["name"])

# Ungrouped folios (no group assigned yet) — show flat below groups
if _ungrouped:
    st.sidebar.markdown(
        "<div style='font-size:11px;font-weight:700;letter-spacing:1.1px;"
        "text-transform:uppercase;color:#8a97a8;padding:6px 6px 2px;'>Ungrouped</div>",
        unsafe_allow_html=True,
    )
    for _lbl, _sc in _ungrouped:
        _nav_btn(_lbl, f"nav_{_sc['id']}", tooltip=_sc["name"])

nav = st.session_state["nav"]


# ── Master Dashboard ───────────────────────────────────────────────────────

def render_master_dashboard():
    st.title("Master Smallcase Dashboard")
    st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    if not all_sc:
        st.info("Create your first smallcase from the sidebar to get started.")
        return

    # ── Master Search ────────────────────────────────────────────────────────
    st.subheader("🔍 Master Search")
    search_query = st.text_input(
        "Search any stock across all folios",
        placeholder="Type stock name or ticker e.g. SBILIFE, Infosys...",
        key="master_search_input",
    )
    if search_query and len(search_query) >= 2:
        try:
            results = db.search_holdings(search_query)
        except Exception as _se:
            st.error(f"Search error: {_se}")
            results = []
        if results:
            live_tickers = list({r["ticker"] for r in results})
            live_data = fin.fetch_live_data(live_tickers)
            sr_rows = []
            for r in results:
                ld = live_data.get(r["ticker"], fin._empty_quote())
                cp = ld["current_price"] if ld["current_price"] > 0 else r["buy_price"]
                invested = round(r["units"] * r["buy_price"], 2)
                mkt_val  = round(r["units"] * cp, 2)
                pnl      = round(mkt_val - invested, 2)
                sr_rows.append({
                    "Group":      r["group_name"] or "—",
                    "Folio":      r["sc_name"],
                    "Stock":      r["scrip_name"],
                    "Ticker":     r["ticker"],
                    "Wt %":       r["weightage"],
                    "Units":      round(r["units"], 2),
                    "Buy Price":  r["buy_price"],
                    "Cur Price":  cp,
                    "Invested":   invested,
                    "Mkt Value":  mkt_val,
                    "P/L":        pnl,
                    "P/L %":      round(pnl / invested * 100, 2) if invested > 0 else 0,
                })
            sr_df = pd.DataFrame(sr_rows)
            st.success(f"Found **{len(sr_df)}** position(s) matching **'{search_query}'**")
            st.dataframe(
                sr_df.style
                    .map(color_pnl, subset=["P/L", "P/L %"])
                    .format({
                        "Wt %":      "{:.1f}%",
                        "Units":     "{:.2f}",
                        "Buy Price": "₹{:,.2f}",
                        "Cur Price": "₹{:,.2f}",
                        "Invested":  "₹{:,.0f}",
                        "Mkt Value": "₹{:,.0f}",
                        "P/L":       "₹{:,.0f}",
                        "P/L %":     "{:.2f}%",
                    }),
                width="stretch", hide_index=True,
            )
        else:
            st.warning(f"No active holdings found matching '{search_query}'")

    st.markdown("---")

    # Aggregate data across all live (non-design) smallcases
    total_invested = 0
    total_market_val = 0
    total_unrealized = 0
    total_realized = 0
    sector_data = {}
    sc_summaries = []   # flat list for all smallcases
    group_totals = {}   # group_name → aggregated metrics

    for sc in all_sc:
        if sc["is_design_mode"]:
            continue
        realized = db.get_realized_pnl(sc["id"])["total_realized"]
        holdings = db.get_holdings(sc["id"])

        if not holdings.empty:
            table = build_holdings_table(holdings, sc["total_investable_amount"])
        else:
            table = pd.DataFrame()

        if not table.empty:
            inv = table["Invested Amount"].sum()
            mv  = table["Market Value"].sum()
            pl  = table["P/L"].sum()
        else:
            inv = mv = pl = 0

        if inv == 0 and realized == 0:
            continue

        total_invested    += inv
        total_market_val  += mv
        total_unrealized  += pl
        total_realized    += realized

        if not table.empty:
            for _, row in table.iterrows():
                ind = row["Industry"] if row["Industry"] else "Unknown"
                sector_data[ind] = sector_data.get(ind, 0) + row["Market Value"]

        combined_pl = pl + realized
        grp = sc.get("group_name") or "Ungrouped"
        sc_summaries.append({
            "Group":        grp,
            "Folio":        sc["name"],
            "Invested":     inv,
            "Market Value": mv,
            "Unrealized P/L": pl,
            "Realized P/L": realized,
            "Total P/L":    combined_pl,
            "Total P/L %":  round(combined_pl / inv * 100, 2) if inv > 0 else 0,
            "Stocks":       len(table) if not table.empty else 0,
        })

        # Group-level rollup
        if grp not in group_totals:
            group_totals[grp] = {"inv": 0, "mv": 0, "unreal": 0, "real": 0}
        group_totals[grp]["inv"]    += inv
        group_totals[grp]["mv"]     += mv
        group_totals[grp]["unreal"] += pl
        group_totals[grp]["real"]   += realized

    # ── Top-level metric cards ────────────────────────────────────────────────
    total_pnl = total_unrealized + total_realized
    pnl_pct   = round(total_pnl / total_invested * 100, 2) if total_invested > 0 else 0
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: metric_card("Total Invested",   format_inr(total_invested))
    with col2: metric_card("Current Value",    format_inr(total_market_val),
                            "profit" if total_market_val >= total_invested else "loss")
    with col3: metric_card("Unrealized P/L",   format_inr(total_unrealized),
                            "profit" if total_unrealized >= 0 else "loss")
    with col4: metric_card("Realized P/L",     format_inr(total_realized),
                            "profit" if total_realized >= 0 else "loss")
    with col5: metric_card("Total P/L",
                            f"{format_inr(total_pnl)} ({pnl_pct}%)",
                            "profit" if total_pnl >= 0 else "loss")

    st.markdown("---")

    # ── Group & Folio breakdown ───────────────────────────────────────────────
    if sc_summaries:
        st.subheader("Portfolio Breakdown by Group")

        groups_sorted = sorted(group_totals.keys())
        for grp in groups_sorted:
            gt = group_totals[grp]
            g_total_pl = gt["unreal"] + gt["real"]
            g_pl_pct   = round(g_total_pl / gt["inv"] * 100, 2) if gt["inv"] > 0 else 0
            color_cls  = "profit" if g_total_pl >= 0 else "loss"

            # Group header with summary
            with st.expander(
                f"**{grp}**  ·  Invested {format_inr(gt['inv'])}  ·  "
                f"MktVal {format_inr(gt['mv'])}  ·  "
                f"Total P/L {format_inr(g_total_pl)} ({g_pl_pct}%)",
                expanded=True,
            ):
                grp_folios = [s for s in sc_summaries if s["Group"] == grp]
                grp_df = pd.DataFrame(grp_folios).drop(columns=["Group"])
                st.dataframe(
                    grp_df.style
                        .map(color_pnl, subset=["Unrealized P/L", "Realized P/L",
                                                "Total P/L", "Total P/L %"])
                        .format({
                            "Invested":       "₹{:,.0f}",
                            "Market Value":   "₹{:,.0f}",
                            "Unrealized P/L": "₹{:,.0f}",
                            "Realized P/L":   "₹{:,.0f}",
                            "Total P/L":      "₹{:,.0f}",
                            "Total P/L %":    "{:.2f}%",
                        }),
                    width="stretch", hide_index=True,
                )

        st.markdown("---")

        col_left, col_right = st.columns([3, 2])
        with col_left:
            st.subheader("All Folios — Combined View")
            all_df = pd.DataFrame(sc_summaries)
            st.dataframe(
                all_df.style
                    .map(color_pnl, subset=["Unrealized P/L", "Realized P/L",
                                            "Total P/L", "Total P/L %"])
                    .format({
                        "Invested":       "₹{:,.0f}",
                        "Market Value":   "₹{:,.0f}",
                        "Unrealized P/L": "₹{:,.0f}",
                        "Realized P/L":   "₹{:,.0f}",
                        "Total P/L":      "₹{:,.0f}",
                        "Total P/L %":    "{:.2f}%",
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
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0", height=450,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(font=dict(size=9), orientation="h",
                                yanchor="top", y=-0.1, xanchor="center", x=0.5),
                )
                st.plotly_chart(fig, use_container_width=True)

    # Capital allocation bar chart
    if sc_summaries:
        st.subheader("Capital Allocation by Folio")
        alloc_df = pd.DataFrame(sc_summaries)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=alloc_df["Folio"], y=alloc_df["Invested"],
                             name="Invested",     marker_color="#5c6bc0"))
        fig.add_trace(go.Bar(x=alloc_df["Folio"], y=alloc_df["Market Value"],
                             name="Market Value", marker_color="#26a69a"))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0", height=350,
            margin=dict(t=20, b=40),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2d2d44"),
        )
        st.plotly_chart(fig, width="stretch")


# ── R Wadiwala Transaction Statement helpers ───────────────────────────────

def _parse_rw_xls(file_bytes: bytes):
    """
    Parse R Wadiwala transaction statement.
    Supports HTML-disguised .xls and real .xlsx files.
    Uses only stdlib html.parser + openpyxl (already a dependency) — no lxml/html5lib needed.
    Returns (scheme_name: str, holdings: list[dict], date_range: str).
    holdings dicts have keys: scrip_name, group, net_qty, avg_cost, invested.
    """
    import io as _io, re as _re
    from html.parser import HTMLParser

    class _TableParser(HTMLParser):
        """Extract all HTML tables using Python stdlib — zero external deps."""
        def __init__(self):
            super().__init__()
            self.tables: list = []
            self._table: list = []
            self._row: list = []
            self._cell: list = []
            self._in_cell = False

        def handle_starttag(self, tag, attrs):
            if tag == 'table':
                self._table = []
            elif tag == 'tr':
                self._row = []
            elif tag in ('td', 'th'):
                self._cell = []
                self._in_cell = True

        def handle_endtag(self, tag):
            if tag in ('td', 'th'):
                self._row.append(''.join(self._cell).strip())
                self._in_cell = False
            elif tag == 'tr' and self._row:
                self._table.append(self._row[:])
                self._row = []
            elif tag == 'table' and self._table:
                self.tables.append(self._table[:])
                self._table = []

        def handle_data(self, data):
            if self._in_cell:
                self._cell.append(data)

    df = None

    # Strategy 1 — HTML-formatted XLS (stdlib html.parser, no external deps)
    try:
        text = file_bytes.decode('utf-8', errors='replace')
        parser = _TableParser()
        parser.feed(text)
        if parser.tables:
            raw = parser.tables[0]
            max_cols = max((len(r) for r in raw), default=0)
            padded = [r + [''] * (max_cols - len(r)) for r in raw]
            df = pd.DataFrame(padded)
    except Exception:
        pass

    # Strategy 2 — Real Excel file (.xlsx via openpyxl, already in requirements)
    if df is None:
        try:
            df = pd.read_excel(_io.BytesIO(file_bytes), header=None, engine='openpyxl')
        except Exception:
            pass

    if df is None or df.empty:
        raise ValueError(
            "Could not parse the file. Tried HTML and Excel formats. "
            "Make sure it is the R Wadiwala Transaction Statement (.xls or .xlsx)."
        )

    # Extract scheme name and date range from header row
    header_text = str(df.iloc[0, 0])
    scheme_name = ""
    date_range = ""

    sm = _re.search(r'Scheme:\s*(.+?)\s*As On Date', header_text)
    if sm:
        parts = [p.strip() for p in sm.group(1).split('-') if p.strip()]
        non_meta = [p for p in parts if p.lower() not in ('advisory', 'research', 'research anlaytics')]
        scheme_name = non_meta[-1] if non_meta else sm.group(1).strip()

    dm = _re.search(r'As On Date:?\s*(\S+)\s*[-–]\s*(\S+)', header_text)
    if dm:
        date_range = f"{dm.group(1)} to {dm.group(2)}"

    def _num(v):
        """Parse a numeric cell that may carry thousands separators, currency
        symbols or parenthesised negatives. Statements format amounts over 999
        as '1,234.56', which a bare float() would reject."""
        if v is None:
            return None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        s = str(v).strip()
        if not s or s.lower() in ('nan', 'none', '-'):
            return None
        neg = s.startswith('(') and s.endswith(')')
        if neg:
            s = s[1:-1]
        s = (s.replace(',', '').replace('₹', '')
              .replace('Rs.', '').replace('Rs', '').strip())
        try:
            f = float(s)
        except ValueError:
            return None
        return -f if neg else f

    # Parse transaction rows
    data_rows, current_group = [], None
    skipped_rows = []
    for _, row in df.iterrows():
        val = str(row[0]).strip()
        if val.startswith('Group:'):
            current_group = val.replace('Group:', '').strip()
        elif val in ('Group Total', 'Grand Total') or 'Client:' in val or val == 'Scrip Name':
            continue
        elif pd.notna(row[1]) and str(row[1]).strip() not in ('Transaction Date', 'NaN', 'nan', ''):
            qty, rate, amount = _num(row[3]), _num(row[4]), _num(row[5])
            if qty is None or amount is None:
                # Never drop silently — a discarded row corrupts the holdings.
                skipped_rows.append(f"{val} | {row[1]} | qty={row[3]!r} amt={row[5]!r}")
                continue
            data_rows.append({
                'group': current_group,
                'scrip': val,
                'date': str(row[1]).strip(),
                'type': str(row[2]).strip(),
                'qty': qty,
                'rate': rate if rate is not None else 0.0,
                'amount': amount,
            })

    if not data_rows:
        raise ValueError("No transaction rows found in the file. Is this the correct format?")

    # Process ALL groups (Equity + Mutual Fund + any others)
    # so the total invested matches the full capital deployed
    hmap: dict = {}
    hmap_group: dict = {}
    for r in data_rows:
        s = r['scrip']
        if s not in hmap:
            hmap[s] = {'buy_qty': 0.0, 'buy_amt': 0.0, 'sell_qty': 0.0}
            hmap_group[s] = r.get('group') or ''
        if r['type'] == 'Buy':
            hmap[s]['buy_qty'] += r['qty']
            hmap[s]['buy_amt'] += abs(r['amount'])
        elif r['type'] in ('Sale', 'Sell'):
            hmap[s]['sell_qty'] += r['qty']

    holdings = []
    for scrip, h in sorted(hmap.items()):
        net_qty = round(h['buy_qty'] - h['sell_qty'], 4)
        avg_cost = round(h['buy_amt'] / h['buy_qty'], 4) if h['buy_qty'] > 0 else 0.0
        holdings.append({
            'scrip_name': scrip,
            'group': hmap_group.get(scrip, ''),
            'buy_qty': h['buy_qty'],
            'sell_qty': h['sell_qty'],
            'net_qty': net_qty,
            'avg_cost': avg_cost,
            'invested': round(avg_cost * net_qty, 2) if net_qty > 0 else 0.0,
        })

    meta = {
        'txn_count': len(data_rows),
        'skipped_rows': skipped_rows,
    }
    return scheme_name, holdings, date_range, meta


def _render_rw_import(sc: dict, sc_id: int, total_amount: float):
    """Render the R Wadiwala transaction statement import panel."""
    with st.container(border=True):
        st.markdown(
            "Upload the **Transaction Statement (.xls)** received from R Wadiwala. "
            "The system will calculate current holdings (net quantity & weighted avg cost) "
            "from all Buy/Sell transactions and **replace** existing holdings in this folio."
        )
        st.warning(
            "⚠️ Importing will **delete all existing active holdings** in this folio "
            "and replace them with calculated data from the statement."
        )

        uploaded = st.file_uploader(
            "Upload R Wadiwala Transaction Statement (.xls)",
            type=["xls", "xlsx", "html"],
            key=f"rw_upload_{sc_id}",
        )

        if not uploaded:
            return

        try:
            raw_bytes = uploaded.read()
            scheme_name, holdings_raw, date_range, parse_meta = _parse_rw_xls(raw_bytes)

            if not holdings_raw:
                st.error("No holdings found in the statement.")
                return

            # Surface any rows we could not read — silently dropping them would
            # corrupt the computed holdings.
            bad_rows = parse_meta.get('skipped_rows') or []
            if bad_rows:
                st.error(
                    f"⚠️ {len(bad_rows)} transaction row(s) could not be read and were "
                    "excluded. The holdings below may be incomplete."
                )
                with st.expander("Show unreadable rows"):
                    st.code("\n".join(bad_rows), language="text")

            # Build scrip→ticker map from existing holdings in this folio
            existing_h = db.get_holdings(sc_id, active_only=False)
            scrip_to_ticker: dict[str, str] = {}
            if not existing_h.empty:
                for _, row in existing_h.iterrows():
                    sn = (row.get('scrip_name') or '').strip().upper()
                    tk = (row.get('ticker') or '').strip()
                    if sn and tk:
                        scrip_to_ticker[sn] = tk

            # Build editable table
            edit_rows = []
            for h in holdings_raw:
                ticker_guess = scrip_to_ticker.get(h['scrip_name'].upper(), '')
                edit_rows.append({
                    'Include': h['net_qty'] > 0,
                    'Group': h.get('group', ''),
                    'Scrip Name': h['scrip_name'],
                    'NSE Ticker': ticker_guess,
                    'Bought': h.get('buy_qty', 0),
                    'Sold': h.get('sell_qty', 0),
                    'Net Qty': h['net_qty'],
                    'Avg Cost (₹)': h['avg_cost'],
                    'Invested (₹)': h['invested'],
                })

            edit_df = pd.DataFrame(edit_rows)

            active_count = sum(1 for r in edit_rows if r['Net Qty'] > 0)
            exited_count = sum(1 for r in edit_rows if r['Net Qty'] == 0)
            negative_rows = [r for r in edit_rows if r['Net Qty'] < 0]
            total_all = sum(r['Invested (₹)'] for r in edit_rows if r['Net Qty'] > 0)

            st.markdown(
                f"**Scheme:** {scheme_name} | **Period:** {date_range} | "
                f"**{parse_meta.get('txn_count', 0)}** transactions read | "
                f"**{active_count}** open, **{exited_count}** fully exited | "
                f"**Total invested: ₹{total_all:,.2f}**"
            )

            if negative_rows:
                names = ", ".join(r['Scrip Name'] for r in negative_rows)
                st.warning(
                    f"⚠️ **{len(negative_rows)} holding(s) sold more than bought within this "
                    f"statement period**: {names}.\n\n"
                    "This means shares were purchased **before** the statement's start date, "
                    "so this file alone cannot determine their true cost. They are excluded "
                    "by default. To capture them, re-download the statement with a start date "
                    "covering the original purchase."
                )

            st.caption(
                "Only holdings with **Net Qty > 0** are ticked — these are your current "
                "positions. Fill in the **NSE Ticker** for each; stocks already in this folio "
                "are auto-filled. Untick anything you want to skip (e.g. the liquid sweep fund)."
            )

            edited = st.data_editor(
                edit_df,
                column_config={
                    'Include': st.column_config.CheckboxColumn('Include', width='small'),
                    'Group': st.column_config.TextColumn('Group', disabled=True, width='small'),
                    'Scrip Name': st.column_config.TextColumn('Scrip Name', disabled=True, width='large'),
                    'NSE Ticker': st.column_config.TextColumn(
                        'NSE Ticker', width='medium',
                        help="NSE ticker symbol without .NS suffix (e.g., MANINDS, HFCL, SCI)."
                    ),
                    'Bought': st.column_config.NumberColumn('Bought', disabled=True, format='%.0f', width='small'),
                    'Sold': st.column_config.NumberColumn('Sold', disabled=True, format='%.0f', width='small'),
                    'Net Qty': st.column_config.NumberColumn('Net Qty', disabled=True, format='%.0f', width='small'),
                    'Avg Cost (₹)': st.column_config.NumberColumn('Avg Cost (₹)', disabled=True, format='%.2f'),
                    'Invested (₹)': st.column_config.NumberColumn('Invested (₹)', disabled=True, format='%.2f'),
                },
                use_container_width=True,
                hide_index=True,
                key=f"rw_edit_{sc_id}",
                num_rows='fixed',
            )

            to_import = edited[edited['Include'] & (edited['Net Qty'] > 0)].copy()
            missing_tickers = to_import[to_import['NSE Ticker'].str.strip() == '']

            if not missing_tickers.empty:
                st.warning(
                    f"⚠️ {len(missing_tickers)} stock(s) need an NSE Ticker before importing: "
                    + ', '.join(missing_tickers['Scrip Name'].tolist())
                )

            total_invested = float(to_import['Invested (₹)'].sum())

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f"**{len(to_import)}** holdings to import | "
                    f"Total invested: **₹{total_invested:,.2f}**"
                )
            with col_btn:
                can_import = missing_tickers.empty and not to_import.empty
                if st.button(
                    "✅ Confirm Import",
                    key=f"rw_confirm_{sc_id}",
                    disabled=not can_import,
                    type="primary",
                ):
                    # Clear all existing active holdings
                    db.delete_all_active_holdings(sc_id)

                    # Insert calculated holdings
                    for _, row in to_import.iterrows():
                        ticker = row['NSE Ticker'].strip().upper()
                        qty = float(row['Net Qty'])
                        avg = float(row['Avg Cost (₹)'])
                        inv = float(row['Invested (₹)'])
                        wt = round(inv / total_invested * 100, 2) if total_invested > 0 else 0.0
                        db.add_holding(
                            smallcase_id=sc_id,
                            ticker=ticker,
                            scrip_name=row['Scrip Name'],
                            industry='',
                            weightage=wt,
                            buy_price=avg,
                            buy_date=date.today().strftime('%Y-%m-%d'),
                            units=qty,
                            stop_loss=0.0,
                        )

                    # Sync total investable amount to statement total
                    db.update_smallcase(sc_id, total_investable_amount=total_invested)
                    st.cache_data.clear()
                    st.success(
                        f"✅ Imported {len(to_import)} holdings. "
                        f"Investable amount updated to ₹{total_invested:,.2f}"
                    )
                    st.rerun()

        except Exception as e:
            st.error(f"Error parsing file: {e}")
            import traceback
            st.code(traceback.format_exc())


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
        confirm_key = f"confirm_del_{sc_id}"
        if st.session_state.get(confirm_key):
            st.caption(f"Delete **{sc['name']}**?")
            dc1, dc2 = st.columns(2)
            if dc1.button("✅ Yes", key=f"del_yes_{sc_id}", type="primary"):
                db.delete_smallcase(sc_id)
                st.session_state.pop(confirm_key, None)
                st.session_state["nav"] = "🏠 Master Dashboard"
                st.rerun()
            if dc2.button("✖ No", key=f"del_no_{sc_id}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
        else:
            if st.button("🗑️ Delete", key=f"del_{sc_id}",
                         help="Permanently deletes this folio and all its holdings"):
                st.session_state[confirm_key] = True
                st.rerun()

    # ── Group assignment row ────────────────────────────────────────────────
    gcol1, gcol2 = st.columns([2, 4])
    with gcol1:
        # Collect all existing group names for a handy dropdown
        existing_groups = sorted({
            s.get("group_name", "").strip()
            for s in db.get_all_smallcases()
            if s.get("group_name", "").strip()
        })
        current_group = (sc.get("group_name") or "").strip()
        # Selectbox with "＋ New group…" option + current value pre-selected
        options = existing_groups if existing_groups else []
        if current_group and current_group not in options:
            options = [current_group] + options
        options_with_new = options + ["＋ New group…"]
        default_idx = options_with_new.index(current_group) if current_group in options_with_new else 0
        chosen = st.selectbox(
            "📂 Group",
            options=options_with_new,
            index=default_idx,
            key=f"grp_sel_{sc_id}",
            help="Assign this folio to a group for the Master Dashboard view",
        )
    with gcol2:
        if chosen == "＋ New group…":
            new_group_name = st.text_input(
                "New group name",
                placeholder="e.g. Smallcase / App / R Wadiwala",
                key=f"grp_new_{sc_id}",
            )
            if st.button("💾 Save Group", key=f"grp_save_{sc_id}"):
                if new_group_name.strip():
                    db.update_smallcase(sc_id, group_name=new_group_name.strip())
                    st.success(f"Group set to '{new_group_name.strip()}'")
                    st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            if chosen != current_group:
                if st.button("💾 Save Group", key=f"grp_save_{sc_id}"):
                    db.update_smallcase(sc_id, group_name=chosen)
                    st.success(f"Group set to '{chosen}'")
                    st.rerun()

    total_amount = new_amount

    # ── Action bar ──────────────────────────────────────────────────────────
    # Compact toggle buttons instead of full-width expanders; the selected
    # panel renders below. Clicking an active button closes it again.
    is_rw = (sc.get("group_name") or "").strip().lower() == "r wadiwala"
    panel_key = f"panel_{sc_id}"
    active_panel = st.session_state.get(panel_key)

    def _panel_button(label: str, name: str, col, help_text: str):
        with col:
            if st.button(
                label, key=f"btn_{name}_{sc_id}", use_container_width=True,
                type="primary" if active_panel == name else "secondary",
                help=help_text,
            ):
                st.session_state[panel_key] = None if active_panel == name else name
                st.rerun()

    btn_cols = st.columns(4)
    i = 0
    if is_rw:
        _panel_button("📋 Import Statement", "rw", btn_cols[i],
                      "Upload the R Wadiwala transaction statement to rebuild holdings")
        i += 1
    _panel_button("➕ Add Stock", "add", btn_cols[i],
                  "Add a new holding to this folio")

    if is_rw and active_panel == "rw":
        _render_rw_import(sc, sc_id, total_amount)

    # ── Add Stock Form ──────────────────────────────────────────────────────
    if active_panel == "add":
        with st.container(border=True):
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

    # ── Holdings Table ──────────────────────────────────────────────────────
    holdings = db.get_holdings(sc_id)
    if holdings.empty:
        st.info("No stocks added yet — use **➕ Add Stock** above to add your first holding.")
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

    # ── Insight strip ───────────────────────────────────────────────────────
    st.markdown("---")
    render_insight_strip(table)

    st.markdown("---")

    # Main holdings table
    hdr_l, hdr_r = st.columns([3, 2])
    with hdr_l:
        st.subheader("Holdings")
    with hdr_r:
        show_all = st.toggle(
            "Show all details", value=False, key=f"cols_all_{sc_id}",
            help="Adds Buy Date, Days Held, XIRR and per-share daily change.",
        )

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
    # Industry is only populated if the user typed it in (no longer auto-fetched)
    has_industry = display_df["Industry"].astype(str).str.strip().ne("").any()

    if show_all:
        final_cols = ["Stock", "Weightage %", "Units", "Buy Date", "Buy Price",
                      "Current Price", "Stop Loss", "🚨 SL Hit",
                      "Invested Amount", "Market Value", "P/L",
                      "P/L %", "Days Held", "XIRR %", "Today Chg", "% Chg", "Industry"]
    else:
        # Compact view: the columns needed to judge a position at a glance
        final_cols = ["Stock", "Weightage %", "Units", "Buy Price", "Current Price",
                      "Stop Loss", "🚨 SL Hit", "Invested Amount", "Market Value",
                      "P/L", "P/L %", "% Chg"]

    if not has_sl:
        final_cols = [c for c in final_cols if c not in ("Stop Loss", "🚨 SL Hit")]
    if not has_industry:
        final_cols = [c for c in final_cols if c != "Industry"]

    display_df = display_df[[c for c in final_cols if c in display_df.columns]]

    def _highlight_sl(row):
        """Turn entire row red if stop loss is triggered."""
        idx = row.name
        if idx < len(sl_flags) and sl_flags[idx]:
            return ["background-color: rgba(255,50,50,0.25); color: #ff8080"] * len(row)
        return [""] * len(row)

    def _pct_or_dash(x):
        """XIRR is blank for same-day/invalid holdings — render as an em dash."""
        return f"{x:.2f}%" if isinstance(x, (int, float)) else "—"

    fmt = {
        "Weightage %": "{:.1f}%",
        "Units": "{:.2f}",
        "Buy Price": "₹{:,.2f}",
        "Current Price": "₹{:,.2f}",
        "Invested Amount": "₹{:,.0f}",
        "Market Value": "₹{:,.0f}",
        "P/L": "₹{:,.0f}",
        "P/L %": "{:.2f}%",
        "XIRR %": _pct_or_dash,
        "Today Chg": "₹{:,.2f}",
        "% Chg": "{:.2f}%",
    }
    if has_sl:
        fmt["Stop Loss"] = lambda x: f"₹{x:,.2f}" if isinstance(x, (int, float)) and x > 0 else ""
    # Restrict to columns actually present in the chosen view
    fmt = {k: v for k, v in fmt.items() if k in display_df.columns}
    pnl_cols = [c for c in ("P/L", "P/L %", "XIRR %", "Today Chg", "% Chg")
                if c in display_df.columns]

    # Keep the stock name visible while scrolling right (Streamlit >= 1.43)
    stock_col_kw = dict(
        help="Click the stock name to open its chart on TradingView",
        display_text=r"#~(.+)$",
        width="medium",
    )
    try:
        stock_col = st.column_config.LinkColumn("Stock 📈", pinned=True, **stock_col_kw)
    except TypeError:
        stock_col = st.column_config.LinkColumn("Stock 📈", **stock_col_kw)

    st.dataframe(
        display_df.style
            .apply(_highlight_sl, axis=1)
            .map(color_pnl, subset=pnl_cols)
            .format(fmt),
        width="stretch", hide_index=True,
        height=min(560, 50 + 35 * len(display_df)),
        column_config={"Stock": stock_col},
    )
    st.caption(
        "Click any column header to sort. "
        + ("Showing all columns." if show_all
           else "Compact view — turn on **Show all details** for Buy Date, Days Held and XIRR.")
    )

    # ── Visual breakdown ────────────────────────────────────────────────────
    with st.expander("📊 Visual Breakdown", expanded=False):
        render_portfolio_charts(table)

    # ── Portfolio statement / export ────────────────────────────────────────
    with st.expander("📄 Portfolio Statement (share / export)", expanded=False):
        st.markdown(f"### {sc['name']} — Portfolio Statement")
        st.caption(f"As on {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Invested", format_inr(total_inv))
        sm2.metric("Market Value", format_inr(total_mv))
        sm3.metric("Total P/L", format_inr(total_pl), f"{total_pl_pct:+.2f}%")
        sm4.metric("Holdings", str(len(table)))

        summary = {
            "Invested": round(float(total_inv), 2),
            "Market Value": round(float(total_mv), 2),
            "Unrealized P/L": round(float(unrealized_pl), 2),
            "Realized P/L": round(float(realized_pl), 2),
            "Total P/L": round(float(total_pl), 2),
            "Total P/L %": round(float(total_pl_pct), 2),
            "Holdings": len(table),
        }

        xls_bytes = build_portfolio_excel(table, sc["name"], summary)
        stamp = datetime.now().strftime("%Y%m%d")
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in sc["name"])
        if xls_bytes:
            st.download_button(
                "⬇️ Download Excel Statement", data=xls_bytes,
                file_name=f"{safe_name}_statement_{stamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"xls_dl_{sc_id}",
            )
        else:
            csv_cols = [c for c in EXPORT_COLS if c in table.columns]
            st.download_button(
                "⬇️ Download CSV Statement",
                data=table[csv_cols].to_csv(index=False).encode("utf-8"),
                file_name=f"{safe_name}_statement_{stamp}.csv",
                mime="text/csv", key=f"csv_dl_{sc_id}",
            )
        st.caption("Tip: use your browser's Print (Ctrl+P) on this page to save a PDF.")

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
                        db.log_transaction(h_id_avg, sc_id, avg_ticker, 'BUY', add_units, add_bp, avg_date_str)

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
                            db.log_transaction(h_id_red, sc_id, red_ticker, 'SELL', sold_units, red_exit_price, red_date_str)

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
        # ── Stock filter + Excel download ───────────────────────────────────
        all_tickers = sorted(txns["ticker"].unique().tolist())
        col_filter, col_dl = st.columns([3, 1])
        with col_filter:
            selected_ticker = st.selectbox(
                "Filter by stock",
                options=["All Stocks"] + all_tickers,
                key=f"txn_filter_{sc_id}",
            )
        # Apply filter
        if selected_ticker == "All Stocks":
            filtered_txns = txns.copy()
        else:
            filtered_txns = txns[txns["ticker"] == selected_ticker].copy()

        # Build display DataFrame
        display_txns = filtered_txns[["transaction_date", "ticker", "action", "units", "price"]].rename(columns={
            "transaction_date": "Date", "ticker": "Ticker", "action": "Action",
            "units": "Units", "price": "Price ₹",
        })
        display_txns["Value ₹"] = (filtered_txns["units"] * filtered_txns["price"]).round(2).values

        st.dataframe(display_txns, width="stretch", hide_index=True)

        # ── Download button (Excel with CSV fallback) ───────────────────────
        file_label = selected_ticker if selected_ticker != "All Stocks" else "All_Stocks"
        sc_name_safe = sc["name"].replace(" ", "_")
        with col_dl:
            st.write("")  # spacing to align with selectbox
            st.write("")
            try:
                import openpyxl  # noqa — ensure it's available
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    export_df = display_txns.copy()
                    export_df.to_excel(writer, index=False, sheet_name="Transactions")
                    ws = writer.sheets["Transactions"]
                    for col_cells in ws.columns:
                        max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col_cells)
                        ws.column_dimensions[col_cells[0].column_letter].width = max(max_len + 2, 12)
                excel_buf.seek(0)
                st.download_button(
                    label="⬇️ Download Excel",
                    data=excel_buf,
                    file_name=f"{sc_name_safe}_{file_label}_transactions.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_txn_{sc_id}_{selected_ticker}",
                )
            except Exception:
                # Fallback to CSV if openpyxl unavailable
                csv_bytes = display_txns.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_bytes,
                    file_name=f"{sc_name_safe}_{file_label}_transactions.csv",
                    mime="text/csv",
                    key=f"dl_txn_{sc_id}_{selected_ticker}",
                )
    else:
        st.info("No transactions recorded yet.")


# ── Mutual Fund Dashboard ────────────────────────────────────────────────────

def render_mutual_funds():
    st.title("📊 Mutual Fund Portfolio")
    st.caption(f"Live NAV from MFAPI.in · Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    try:
        all_mf = db.get_all_mutual_funds()
    except Exception as _e:
        st.error(f"Database error: {_e}")
        return

    # ── Add Fund ────────────────────────────────────────────────────────────
    with st.expander("➕ Add Mutual Fund", expanded=not all_mf):
        st.markdown("**Step 1 — Search for a fund**")
        mf_search_q = st.text_input(
            "Search fund name",
            placeholder="e.g. SBI Bluechip, HDFC Midcap, Parag Parikh...",
            key="mf_search_q",
        )
        search_results = []
        if mf_search_q and len(mf_search_q) >= 3:
            with st.spinner("Searching AMFI database..."):
                search_results = fin.search_mutual_funds(mf_search_q)

        selected_scheme_code = None
        selected_scheme_name = ""
        mf_meta = {}
        if search_results:
            fund_options = {r["schemeName"]: r["schemeCode"] for r in search_results[:40]}
            chosen_name = st.selectbox(
                "Select Fund", options=list(fund_options.keys()), key="mf_sel"
            )
            selected_scheme_code = fund_options[chosen_name]
            selected_scheme_name = chosen_name
            with st.spinner("Fetching fund details..."):
                mf_meta = fin.fetch_mf_nav(selected_scheme_code)
            ci1, ci2, ci3 = st.columns(3)
            ci1.info(f"**AMC:** {mf_meta.get('fund_house') or '—'}")
            ci2.info(f"**Category:** {mf_meta.get('scheme_category') or '—'}")
            ci3.info(f"**Current NAV:** ₹{mf_meta.get('nav', 0):,.4f}  ({mf_meta.get('nav_date', '')})")

        st.markdown("**Step 2 — Enter your investment details**")
        with st.form("add_mf_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                # Invested amount instead of units — units calculated internally
                mf_invested = st.number_input(
                    "Amount Invested (₹)", min_value=0.0, step=1000.0,
                    format="%.2f", key="mf_invested",
                    help="Total ₹ amount you put into this fund",
                )
                mf_avg_nav = st.number_input(
                    "Average Purchase NAV (₹)", min_value=0.0, step=0.01,
                    key="mf_avg_nav",
                    help="Average NAV at which you purchased (check your statement)",
                )
            with fc2:
                mf_date  = st.date_input("Purchase / Start Date", value=date.today(), key="mf_date")
                mf_folio = st.text_input("Folio Number (optional)", key="mf_folio")
            mf_notes  = st.text_input("Notes (optional)", key="mf_notes")
            mf_submit = st.form_submit_button("➕ Add Fund")
            if mf_submit:
                if not selected_scheme_code:
                    st.error("Please search and select a fund first (Step 1).")
                elif mf_invested <= 0 or mf_avg_nav <= 0:
                    st.error("Amount Invested and Average NAV must be greater than 0.")
                else:
                    # Calculate units from invested amount / avg NAV
                    computed_units = round(mf_invested / mf_avg_nav, 4)
                    meta = fin.fetch_mf_nav(selected_scheme_code)
                    db.add_mutual_fund(
                        scheme_code=selected_scheme_code,
                        fund_name=selected_scheme_name,
                        amc=meta.get("fund_house", ""),
                        category=meta.get("scheme_category", ""),
                        units=computed_units,
                        avg_nav=mf_avg_nav,
                        purchase_date=str(mf_date),
                        folio_number=mf_folio,
                        notes=mf_notes,
                    )
                    st.success(f"✅ Added: {selected_scheme_name}  ({computed_units} units @ ₹{mf_avg_nav})")
                    st.rerun()

    if not all_mf:
        st.info("No mutual funds added yet. Use the form above to add your first fund.")
        return

    # ── Fetch live NAVs ─────────────────────────────────────────────────────
    scheme_codes = [mf["scheme_code"] for mf in all_mf if mf.get("scheme_code")]
    with st.spinner("Fetching live NAVs..."):
        nav_data = fin.fetch_mf_nav_batch(scheme_codes)

    # ── Build holdings table ─────────────────────────────────────────────────
    rows = []
    total_invested = 0.0
    total_current  = 0.0
    for mf in all_mf:
        sc       = mf.get("scheme_code")
        nav_info = nav_data.get(sc, {}) if sc else {}
        cur_nav  = float(nav_info.get("nav", 0) or 0)
        units    = float(mf.get("units", 0) or 0)
        avg_nav  = float(mf.get("avg_nav", 0) or 0)
        invested = round(units * avg_nav, 2)
        cur_val  = round(units * cur_nav, 2) if cur_nav > 0 else 0.0
        abs_ret  = round(cur_val - invested, 2)
        pct_ret  = round((abs_ret / invested * 100), 2) if invested > 0 else 0.0
        xirr_val = None
        if cur_nav > 0 and avg_nav > 0 and units > 0:
            xirr_val = fin.calculate_xirr(
                mf.get("purchase_date", ""), avg_nav, units, cur_nav
            )
        total_invested += invested
        total_current  += cur_val
        rows.append({
            "Fund Name":      mf["fund_name"],
            "AMC":            mf.get("amc") or nav_info.get("fund_house", ""),
            "Category":       mf.get("category") or nav_info.get("scheme_category", ""),
            "Avg NAV ₹":     round(avg_nav, 4),
            "Current NAV ₹": round(cur_nav, 4),
            "NAV Date":       nav_info.get("nav_date", ""),
            "Invested ₹":    invested,
            "Cur Value ₹":   cur_val,
            "P/L ₹":         abs_ret,
            "Return %":       pct_ret,
            "XIRR %":         f"{xirr_val:.2f}%" if xirr_val is not None else "—",
            "_id":             mf["id"],
            "_units":          units,
            "_avg_nav":        avg_nav,
            "_folio":          mf.get("folio_number", ""),
        })

    total_pnl = round(total_current - total_invested, 2)
    total_ret = round(total_pnl / total_invested * 100, 2) if total_invested > 0 else 0.0

    # ── Summary metrics ─────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    def _mf_metric(col, label, val, is_pct=False, color="white"):
        if is_pct:
            display = f"{val:+.2f}%"
        else:
            display = f"₹{val:,.0f}"
        col.markdown(
            f"""<div style="background:linear-gradient(135deg,#1e2a3a,#0d1b2a);
            border-radius:12px;padding:18px;text-align:center;border:1px solid #2d4a6a;">
            <p style="color:#8899aa;font-size:11px;letter-spacing:1px;margin:0">{label}</p>
            <p style="color:{color};font-size:22px;font-weight:700;margin:5px 0">{display}</p></div>""",
            unsafe_allow_html=True,
        )
    _mf_metric(m1, "TOTAL INVESTED", total_invested)
    _mf_metric(m2, "CURRENT VALUE", total_current)
    _mf_metric(m3, "TOTAL P/L", total_pnl, color="#4caf50" if total_pnl >= 0 else "#f44336")
    _mf_metric(m4, "OVERALL RETURN", total_ret, is_pct=True,
               color="#4caf50" if total_ret >= 0 else "#f44336")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Holdings table (no Units column shown) ───────────────────────────────
    if rows:
        df = pd.DataFrame(rows)
        display_df = df.drop(columns=["_id", "_units", "_avg_nav", "_folio"])
        st.dataframe(
            display_df.style
                .map(color_pnl, subset=["P/L ₹", "Return %"])
                .format({
                    "Avg NAV ₹":     "₹{:,.4f}",
                    "Current NAV ₹": "₹{:,.4f}",
                    "Invested ₹":    "₹{:,.2f}",
                    "Cur Value ₹":   "₹{:,.2f}",
                    "P/L ₹":         "₹{:,.2f}",
                    "Return %":       "{:.2f}%",
                }),
            width="stretch", hide_index=True,
        )

    # ── Edit / Delete per fund ───────────────────────────────────────────────
    st.subheader("Manage Holdings")
    for row in rows:
        mf_id = row["_id"]
        with st.expander(f"⚙️ {row['Fund Name']}", expanded=False):
            ec1, ec2, ec3, ec4 = st.columns([2, 2, 2, 1])
            # Edit by invested amount — keep units hidden
            cur_invested = round(row["_units"] * row["_avg_nav"], 2)
            new_invested = ec1.number_input(
                "Amount Invested (₹)", value=cur_invested,
                min_value=0.0, step=1000.0, format="%.2f",
                key=f"mfe_inv_{mf_id}",
            )
            new_avg_nav = ec2.number_input(
                "Avg NAV ₹", value=row["_avg_nav"],
                min_value=0.0, step=0.01,
                key=f"mfe_nav_{mf_id}",
            )
            new_folio = ec3.text_input(
                "Folio No.", value=row["_folio"],
                key=f"mfe_folio_{mf_id}",
            )
            ec4.markdown("<br>", unsafe_allow_html=True)
            col_save, col_del = ec4.columns(2)
            if col_save.button("💾", key=f"mfe_save_{mf_id}", help="Save changes"):
                new_units = round(new_invested / new_avg_nav, 4) if new_avg_nav > 0 else 0
                db.update_mutual_fund(mf_id, units=new_units, avg_nav=new_avg_nav,
                                      folio_number=new_folio)
                st.success("Updated!")
                st.rerun()
            if col_del.button("🗑️", key=f"mfe_del_{mf_id}", help="Delete this fund"):
                db.delete_mutual_fund(mf_id)
                st.rerun()

    # ── Excel / CSV download ─────────────────────────────────────────────────
    st.markdown("---")
    try:
        import openpyxl  # noqa
        dl_buf = io.BytesIO()
        with pd.ExcelWriter(dl_buf, engine="openpyxl") as writer:
            pd.DataFrame(rows).drop(columns=["_id", "_units", "_avg_nav", "_folio"]).to_excel(
                writer, index=False, sheet_name="MF Holdings"
            )
        dl_buf.seek(0)
        st.download_button("⬇️ Download Excel", data=dl_buf,
                           file_name="mutual_fund_holdings.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception:
        csv_bytes = (pd.DataFrame(rows)
                     .drop(columns=["_id", "_units", "_avg_nav", "_folio"])
                     .to_csv(index=False).encode())
        st.download_button("⬇️ Download CSV", data=csv_bytes,
                           file_name="mutual_fund_holdings.csv", mime="text/csv")


# ── Router ──────────────────────────────────────────────────────────────────

if nav == "🏠 Master Dashboard":
    render_master_dashboard()
elif nav == "📊 Mutual Funds":
    render_mutual_funds()
else:
    # Find the matching smallcase
    for sc in all_sc:
        label = f"{'🧪' if sc['is_design_mode'] else '📁'} {sc['name']}"
        if nav == label:
            render_smallcase(sc)
            break
