import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

from utils.auth import login_screen
from utils.data_loader import load_data, latest_snapshot
from utils.analytics import build_reorder_table, forecast_product, discount_analysis
from utils.cpp_engine import ensure_engine, run_engine

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "dataset" / "sales_data.csv"

st.set_page_config(
    page_title="Smart Inventory | Stock & Demand",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

def apply_styles():
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

apply_styles()

if not st.session_state.get("authenticated", False):
    login_screen()
    st.stop()

@st.cache_data(show_spinner="Loading inventory dataset...")
def get_data():
    return load_data(DATA_PATH)

try:
    data = get_data()
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

snapshot = latest_snapshot(data)
latest_date = data["Date"].max()
low_stock_cutoff = 50

with st.sidebar:
    st.markdown("<div class='brand-mark'>📦</div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-title'>STOCKWISE</div>", unsafe_allow_html=True)
    st.caption("Retail inventory intelligence")
    st.divider()
    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Product & Inventory",
            "Sales Tracking",
            "Smart Reorder",
            "Demand Forecasting",
            "Price & Discount Analysis",
        ],
        label_visibility="visible",
    )
    st.divider()
    st.markdown(f"**Dataset updated through**  \n{latest_date:%d %b %Y}")
    st.caption("Read-only historical dataset")
    if st.button("Log out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown(
    f"<div class='page-kicker'>RETAIL INVENTORY MANAGEMENT</div>"
    f"<h1 class='page-heading'>{page}</h1>",
    unsafe_allow_html=True,
)

# Compile the C++ DSA engine when a compiler is available.
engine_ok, engine_message = ensure_engine(ROOT)

if page == "Dashboard":
    st.markdown("A consolidated view of stock, sales and demand across all stores.")
    total_products = snapshot["Product ID"].nunique()
    total_stock = int(snapshot["Inventory Level"].sum())
    low_count = int((snapshot["Inventory Level"] <= low_stock_cutoff).sum())
    recent_start = latest_date - pd.Timedelta(days=29)
    recent = data[data["Date"] >= recent_start]
    recent_sales = int(recent["Units Sold"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", f"{total_products:,}")
    c2.metric("Current stock", f"{total_stock:,} units")
    c3.metric("Low-stock records", f"{low_count:,}")
    c4.metric("Units sold · last 30 days", f"{recent_sales:,}")

    left, right = st.columns([1.45, 1])
    with left:
        st.markdown("#### Daily units sold")
        daily_sales = data.groupby("Date", as_index=True)["Units Sold"].sum().tail(60)
        st.line_chart(daily_sales, height=280)
    with right:
        st.markdown("#### Current stock by category")
        category_stock = snapshot.groupby("Category")["Inventory Level"].sum().sort_values(ascending=False)
        st.bar_chart(category_stock, height=280)

    st.markdown("#### Inventory snapshot by store")
    store_summary = snapshot.groupby("Store ID").agg(
        Products=("Product ID", "nunique"),
        Available_Stock=("Inventory Level", "sum"),
        Units_Sold=("Units Sold", "sum"),
    ).reset_index().rename(columns={
        "Store ID": "Store",
        "Available_Stock": "Available stock",
        "Units_Sold": "Units sold on latest date",
    })
    st.dataframe(store_summary, use_container_width=True, hide_index=True)
    st.caption("Current stock means the latest recorded Inventory Level for each store-product pair.")

elif page == "Product & Inventory":
    st.markdown("Search the historical inventory records. This section does not edit the source dataset.")
    col1, col2, col3 = st.columns([1, 1, 1.4])
    with col1:
        store_options = ["All stores"] + sorted(snapshot["Store ID"].unique().tolist())
        selected_store = st.selectbox("Store", store_options)
    with col2:
        categories = ["All categories"] + sorted(snapshot["Category"].unique().tolist())
        selected_category = st.selectbox("Category", categories)
    with col3:
        product_query = st.text_input("Search Product ID", placeholder="e.g. P0001").strip().upper()

    view = snapshot.copy()
    if selected_store != "All stores":
        view = view[view["Store ID"] == selected_store]
    if selected_category != "All categories":
        view = view[view["Category"] == selected_category]
    if product_query:
        view = view[view["Product ID"].str.contains(product_query, case=False, na=False)]

    display = view[[
        "Store ID", "Product ID", "Category", "Region", "Inventory Level",
        "Units Sold", "Units Ordered", "Price", "Discount", "Demand", "Date"
    ]].sort_values(["Store ID", "Product ID"])
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(f"{len(display):,} latest store-product records shown. Dataset is read-only.")

    if product_query and engine_ok:
        st.markdown("#### C++ product lookup")
        result = run_engine(ROOT, "search", str(DATA_PATH), product_query)
        if result.strip():
            rows = [line.split("\t") for line in result.strip().splitlines() if line.strip()]
            if rows and len(rows[0]) >= 6:
                cpp_df = pd.DataFrame(rows, columns=[
                    "Store", "Product", "Inventory", "Units sold", "Demand", "Date"
                ])
                st.dataframe(cpp_df, use_container_width=True, hide_index=True)
        else:
            st.info("No matching product was found by the C++ lookup engine.")
    elif product_query and not engine_ok:
        st.info("C++ lookup is unavailable until the compiler setup in README is completed.")

elif page == "Sales Tracking":
    st.markdown("Explore recorded sales across the available dates, stores and product categories.")
    min_date, max_date = data["Date"].min().date(), data["Date"].max().date()
    chosen_dates = st.date_input(
        "Date range",
        value=(max(min_date, max_date - pd.Timedelta(days=29)), max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(chosen_dates, tuple) and len(chosen_dates) == 2:
        start_date, end_date = chosen_dates
    else:
        start_date, end_date = min_date, max_date
    sales_view = data[
        (data["Date"].dt.date >= start_date) &
        (data["Date"].dt.date <= end_date)
    ]
    s1, s2, s3 = st.columns(3)
    s1.metric("Units sold", f"{int(sales_view['Units Sold'].sum()):,}")
    s2.metric("Recorded demand", f"{int(sales_view['Demand'].sum()):,}")
    s3.metric("Active store-product records", f"{len(sales_view):,}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Units sold by category")
        st.bar_chart(sales_view.groupby("Category")["Units Sold"].sum().sort_values(ascending=False))
    with col_b:
        st.markdown("#### Units sold by region")
        st.bar_chart(sales_view.groupby("Region")["Units Sold"].sum().sort_values(ascending=False))
    st.markdown("#### Best-selling products in selected period")
    top_products = sales_view.groupby("Product ID")["Units Sold"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(top_products)
    st.dataframe(
        top_products.rename("Total units sold").reset_index(),
        use_container_width=True,
        hide_index=True,
    )

elif page == "Smart Reorder":
    st.markdown(
        "The system compares the latest recorded stock with recent demand to identify products "
        "that may need replenishment. No records are changed."
    )
    lead_days = st.slider("Assumed supplier lead time (days)", 1, 21, 7)
    coverage_days = st.slider("Target stock coverage (days)", 7, 30, 14)
    reorder_df = build_reorder_table(data, snapshot, lead_days, coverage_days)
    flagged = reorder_df[reorder_df["Inventory Level"] <= reorder_df["Reorder Point"]].copy()
    a, b, c = st.columns(3)
    a.metric("Store-product combinations", f"{len(reorder_df):,}")
    b.metric("Reorder alerts", f"{len(flagged):,}")
    c.metric("Lead time assumption", f"{lead_days} days")
    if flagged.empty:
        st.success("No products currently fall below the calculated reorder point.")
    else:
        st.warning("The following store-product combinations are at or below their calculated reorder point.")
        st.dataframe(
            flagged[[
                "Store ID", "Product ID", "Category", "Inventory Level",
                "Avg Daily Demand", "Reorder Point", "Suggested Order Qty"
            ]].sort_values("Inventory Level"),
            use_container_width=True,
            hide_index=True,
        )
    with st.expander("How is the reorder point calculated?"):
        st.write(
            "Average daily demand and demand variability are calculated from the latest 30 days "
            "for each store-product pair. Reorder Point = average daily demand × lead time + "
            "safety stock. Safety stock uses 1.65 × daily demand standard deviation × √lead time. "
            "Suggested Order Qty targets the selected number of days of demand coverage."
        )
    st.caption("This is a transparent rule-based estimate, not a supplier-confirmed order quantity.")

elif page == "Demand Forecasting":
    st.markdown("A simple historical-demand forecast using the latest seven recorded days.")
    store = st.selectbox("Select store", sorted(data["Store ID"].unique().tolist()))
    products = sorted(data.loc[data["Store ID"] == store, "Product ID"].unique().tolist())
    product = st.selectbox("Select product", products)
    result = forecast_product(data, store, product)
    if result is None or result.empty:
        st.info("There is not enough historical data for this selection.")
    else:
        last_avg = float(result["Demand"].tail(7).mean())
        next_week = max(0, int(round(last_avg * 7)))
        m1, m2, m3 = st.columns(3)
        m1.metric("Average daily demand · last 7 days", f"{last_avg:.1f} units")
        m2.metric("Estimated next 7 days", f"{next_week:,} units")
        m3.metric("Latest recorded inventory", f"{int(result['Inventory Level'].iloc[-1]):,} units")
        st.markdown("#### Historical demand")
        chart = result.set_index("Date")[["Demand", "7-day average"]]
        st.line_chart(chart, height=330)
        st.caption(
            "Forecast method: the mean demand from the latest seven recorded days is carried "
            "forward as a simple baseline. It is intended for a mini-project demonstration, "
            "not a guarantee of future sales."
        )

elif page == "Price & Discount Analysis":
    st.markdown("Compare recorded sales patterns across discount levels and product prices.")
    discount_df = discount_analysis(data)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Average units sold by discount band")
        st.bar_chart(discount_df.set_index("Discount Band")["Average Units Sold"])
    with col2:
        st.markdown("#### Average demand by discount band")
        st.bar_chart(discount_df.set_index("Discount Band")["Average Demand"])
    st.dataframe(discount_df, use_container_width=True, hide_index=True)
    st.caption(
        "These are historical associations. The charts do not prove that a discount caused "
        "a change in sales or demand."
    )

st.divider()
status = "available" if engine_ok else "not compiled"
st.caption(f"DSA engine (C++): {status} · Data source: dataset/sales_data.csv · Read-only mode")
