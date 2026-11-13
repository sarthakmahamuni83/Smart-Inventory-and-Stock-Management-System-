import pandas as pd
import streamlit as st

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    required = [
        "Date", "Store ID", "Product ID", "Category", "Region",
        "Inventory Level", "Units Sold", "Units Ordered", "Price",
        "Discount", "Weather Condition", "Promotion", "Competitor Pricing",
        "Seasonality", "Epidemic", "Demand",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).copy()
    numeric = [
        "Inventory Level", "Units Sold", "Units Ordered", "Price",
        "Discount", "Promotion", "Competitor Pricing", "Epidemic", "Demand",
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["Store ID", "Product ID", "Category", "Region"]:
        df[col] = df[col].astype(str)
    return df.sort_values("Date").reset_index(drop=True)

def latest_snapshot(df):
    return (
        df.sort_values("Date")
          .groupby(["Store ID", "Product ID"], as_index=False)
          .tail(1)
          .copy()
          .sort_values(["Store ID", "Product ID"])
    )
