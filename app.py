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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border-radius: 12px; padding: 20px; text-align: center;
        border: 1px solid #3d3d5c; margin-bottom: 10px;
    }
    .metric-card h3 { color: #a0a0c0; font-size: 13px; margin: 0; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card .value { font-size: 28px; font-weight: 700; margin: 8px 0 0; }
    .profit { color: #00e676 !important; }
    .loss { color: #ff5252 !important; }
    .neutral { color: #ffffff !important; }
    .flag-warning {
        background: #ff52521a; border: 1px solid #ff5252; border-radius: 8px;
        padding: 10px 15px; margin: 5px 0; color: #ff8a80;
    }
    div[data-testid="stSidebar"] { background: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #1e1e2e; border-radius: 8px 8px 0 0;
        padding: 10px 20px; border: 1px solid #3d3d5c;
    }
</style>
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
            "Exit Date": h["exit_date"] if h["exit_date"] else "",
            "Exit Price": h["exit_price"] if h["exit_price"] else "",
        })

    return pd.DataFrame(rows)


# ── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.title("⚡ Smallcase Manager")

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
    total_pnl = 0
    sector_data = {}
    sc_summaries = []

    for sc in all_sc:
        if sc["is_design_mode"]:
            continue
        holdings = db.get_holdings(sc["id"])
        if holdings.empty:
            continue

        table = build_holdings_table(holdings, sc["total_investable_amount"])
        if table.empty:
            continue

        inv = table["Invested Amount"].sum()
        mv = table["Market Value"].sum()
        pl = table["P/L"].sum()
        total_invested += inv
        total_market_val += mv
        total_pnl += pl

        # Sector aggregation
        for _, row in table.iterrows():
            ind = row["Industry"] if row["Industry"] else "Unknown"
            sector_data[ind] = sector_data.get(ind, 0) + row["Market Value"]

        sc_summaries.append({
            "Smallcase": sc["name"],
            "Invested": inv,
            "Market Value": mv,
            "P/L": pl,
            "P/L %": round(pl / inv * 100, 2) if inv > 0 else 0,
            "Stocks": len(table),
        })

    # Top metric cards
    pnl_pct = round(total_pnl / total_invested * 100, 2) if total_invested > 0 else 0
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Invested", format_inr(total_invested))
    with col2:
        metric_card("Current Value", format_inr(total_market_val),
                     "profit" if total_market_val >= total_invested else "loss")
    with col3:
        metric_card("Total P/L", f"{format_inr(total_pnl)} ({pnl_pct}%)",
                     "profit" if total_pnl >= 0 else "loss")
    with col4:
        metric_card("Active Smallcases", str(len(sc_summaries)))

    st.markdown("---")

    # Smallcase performance table
    if sc_summaries:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("Smallcase Performance")
            sum_df = pd.DataFrame(sc_summaries)
            st.dataframe(
                sum_df.style.applymap(color_pnl, subset=["P/L", "P/L %"])
                     .format({
                         "Invested": "₹{:,.0f}",
                         "Market Value": "₹{:,.0f}",
                         "P/L": "₹{:,.0f}",
                         "P/L %": "{:.2f}%",
                     }),
                use_container_width=True, hide_index=True,
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
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0",
                    height=350,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(font=dict(size=10)),
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
        st.plotly_chart(fig, use_container_width=True)


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
            fin._price_cache.clear()
            fin._cache_time = 0
            st.rerun()
    with col_s4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete Smallcase", key=f"del_{sc_id}"):
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

        # Step 2: Form with pre-filled values
        with st.form(f"add_stock_{sc_id}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                scrip_name = st.text_input("Scrip Name", value=default_name)
                industry = st.text_input("Industry / Sector", value=default_industry)
            with c2:
                weightage = st.number_input("Target Weightage %", 0.0, 100.0, 5.0, 0.5)
                buy_price = st.number_input("Buy Price (₹)", 0.0, step=0.5)
            with c3:
                buy_date = st.date_input("Date of Buy", value=date.today())
                auto_calc = st.checkbox("Auto-calculate Units from Weightage", value=True)

            if not auto_calc:
                manual_units = st.number_input("Manual Units", 0.0, step=1.0)

            liq_exit_price = st.number_input(
                "LIQUIDCASE exit price (₹) — for auto-rebalancing",
                min_value=0.0, step=0.1, value=0.0,
                key=f"add_liq_ep_{sc_id}",
                help="If adding this stock reduces LIQUIDCASE allocation, enter the price you sold LIQUIDCASE units at. Leave 0 to use buy price."
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
                    buy_date=buy_date.strftime("%Y-%m-%d"),
                    units=units,
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
        st.info("No stocks added yet. Use the form above to add holdings.")
        return

    table = build_holdings_table(holdings, total_amount, is_design)
    if table.empty:
        st.warning("Could not build table. Check your data.")
        return

    # Summary metrics
    total_inv = table["Invested Amount"].sum()
    total_mv = table["Market Value"].sum()
    total_pl = table["P/L"].sum()
    total_pl_pct = round(total_pl / total_inv * 100, 2) if total_inv > 0 else 0
    total_wt = table["Weightage %"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Invested", format_inr(total_inv))
    with c2:
        metric_card("Market Value", format_inr(total_mv),
                     "profit" if total_mv >= total_inv else "loss")
    with c3:
        metric_card("P/L", f"{format_inr(total_pl)} ({total_pl_pct}%)",
                     "profit" if total_pl >= 0 else "loss")
    with c4:
        metric_card("Stocks", str(len(table)))
    with c5:
        wt_class = "profit" if abs(total_wt - 100) < 1 else "loss"
        metric_card("Total Weightage", f"{total_wt:.1f}%", wt_class)

    st.markdown("---")

    # Main holdings table
    st.subheader("Holdings")
    display_cols = ["Scrip Name", "Ticker", "Industry", "Weightage %", "Units",
                    "Buy Date", "Buy Price", "Current Price", "Invested Amount",
                    "Market Value", "P/L", "P/L %", "Days Held", "XIRR %",
                    "Today Chg", "% Chg"]
    display_df = table[display_cols].copy()

    st.dataframe(
        display_df.style
            .applymap(color_pnl, subset=["P/L", "P/L %", "Today Chg", "% Chg"])
            .format({
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
            }),
        use_container_width=True, hide_index=True, height=min(400, 50 + 35 * len(display_df)),
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
        return row, {
            "wt": float(row["Weightage %"]),
            "bp": float(row["Buy Price"]),
            "ind": str(row["Industry"]),
            "units": float(row["Units"]),
            "inv": float(row["Invested Amount"]),
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
            "> Use this when you increase weightage of a stock at a different price. "
            "The system will calculate new total units and weighted average buy price."
        )
        if stock_options:
            sel_avg = st.selectbox("Select stock to add more", list(stock_options.keys()),
                                   key=f"avg_sel_{sc_id}")
            h_id_avg = stock_options[sel_avg]
            sel_row_avg, cur_avg = _stock_summary(h_id_avg)

            st.caption(
                f"Current: Weightage **{cur_avg['wt']}%** · "
                f"Avg Buy Price **₹{cur_avg['bp']:,.2f}** · "
                f"Units **{cur_avg['units']:.2f}** · "
                f"Invested **₹{cur_avg['inv']:,.2f}**"
            )

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
                        key=f"abp_{sc_id}_{h_id_avg}",
                        help="Price at which you bought the additional quantity"
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
                        "LIQUIDCASE exit price (₹) — for auto-rebalance",
                        min_value=0.0, step=0.1, value=0.0,
                        key=f"aliq_{sc_id}_{h_id_avg}",
                        help="Price at which LIQUIDCASE units are sold to fund this increase. Leave 0 to use buy price."
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
            "> Sell some units to lower a stock's allocation. "
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

                st.caption(
                    f"Current: Weightage **{cur_red['wt']}%** · "
                    f"Avg Buy Price **₹{cur_red['bp']:,.2f}** · "
                    f"Units **{cur_red['units']:.2f}** · "
                    f"Invested **₹{cur_red['inv']:,.2f}**"
                )

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
                            key=f"rep_{sc_id}_{h_id_red}",
                            help="The price at which you sold the excess units"
                        )

                    red_date = st.date_input("Date of Reduction", value=date.today(),
                                             key=f"rdt_{sc_id}_{h_id_red}")

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
                                (h_id_red, sc_id, sel_row_red["Ticker"], sold_units,
                                 red_exit_price, red_date.strftime("%Y-%m-%d"))
                            )
                            conn.commit()
                            conn.close()

                            # Auto-rebalance LIQUIDCASE (freed weightage flows back)
                            rb = db.rebalance_residual(sc_id, total_amount)
                            if rb:
                                st.info(
                                    f"🔄 LIQUIDCASE: {rb['old_wt']:.1f}% → {rb['new_wt']:.1f}% "
                                    f"({rb['delta_units']:+.2f} units)"
                                )

                            st.success(
                                f"Reduced {sel_row_red['Ticker']}: "
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
            with st.form(f"exit_form_{sc_id}"):
                exit_price = st.number_input("Exit Price (₹)", 0.0, key=f"exp_{sc_id}")
                exit_date = st.date_input("Exit Date", value=date.today(), key=f"exd_{sc_id}")
                if st.form_submit_button("Exit Position"):
                    db.exit_holding(h_id_exit, exit_price, exit_date.strftime("%Y-%m-%d"))
                    # Auto-rebalance LIQUIDCASE (freed weightage goes back)
                    if exit_row["Ticker"] != db.RESIDUAL_TICKER:
                        rb = db.rebalance_residual(sc_id, total_amount)
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
    st.subheader("Analytics & Risk Metrics")

    # Fetch stock info for beta, div yield
    tickers = table["Ticker"].tolist()
    weightages = table["Weightage %"].tolist()

    with st.spinner("Fetching stock fundamentals..."):
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
            st.plotly_chart(fig, use_container_width=True)

    # P/L Treemap
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
        st.plotly_chart(fig, use_container_width=True)

    # Transaction log
    st.subheader("Transaction Log")
    txns = db.get_transactions(sc_id)
    if not txns.empty:
        st.dataframe(
            txns[["transaction_date", "ticker", "action", "units", "price"]].rename(columns={
                "transaction_date": "Date", "ticker": "Ticker", "action": "Action",
                "units": "Units", "price": "Price",
            }),
            use_container_width=True, hide_index=True,
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
