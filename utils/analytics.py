import numpy as np
import pandas as pd

def build_reorder_table(df, snapshot, lead_days=7, coverage_days=14):
    latest_date = df["Date"].max()
    recent = df[df["Date"] > latest_date - pd.Timedelta(days=30)]
    demand_stats = recent.groupby(["Store ID", "Product ID"])["Demand"].agg(
        avg_demand="mean", std_demand="std"
    ).reset_index()
    result = snapshot.merge(demand_stats, on=["Store ID", "Product ID"], how="left")
    result["avg_demand"] = result["avg_demand"].fillna(0)
    result["std_demand"] = result["std_demand"].fillna(0)
    result["Reorder Point"] = np.ceil(
        result["avg_demand"] * lead_days
        + 1.65 * result["std_demand"] * np.sqrt(lead_days)
    ).astype(int)
    target_stock = np.ceil(result["avg_demand"] * coverage_days)
    result["Suggested Order Qty"] = np.maximum(
        0, target_stock - result["Inventory Level"]
    ).astype(int)
    result["Avg Daily Demand"] = result["avg_demand"].round(1)
    return result

def forecast_product(df, store, product):
    subset = df[(df["Store ID"] == store) & (df["Product ID"] == product)].copy()
    if subset.empty:
        return None
    subset = subset.sort_values("Date").tail(60)
    subset["7-day average"] = subset["Demand"].rolling(7, min_periods=1).mean().round(1)
    return subset[["Date", "Demand", "7-day average", "Inventory Level"]]

def discount_analysis(df):
    work = df.copy()
    bins = [-0.001, 0, 10, 20, 1000]
    labels = ["0%", "1–10%", "11–20%", "Above 20%"]
    work["Discount Band"] = pd.cut(work["Discount"], bins=bins, labels=labels)
    result = work.groupby("Discount Band", observed=False).agg(
        Records=("Discount", "size"),
        Average_Units_Sold=("Units Sold", "mean"),
        Average_Demand=("Demand", "mean"),
        Average_Price=("Price", "mean"),
    ).reset_index()
    result = result.rename(columns={
        "Average_Units_Sold": "Average Units Sold",
        "Average_Demand": "Average Demand",
        "Average_Price": "Average Price",
    })
    for col in ["Average Units Sold", "Average Demand", "Average Price"]:
        result[col] = result[col].round(2)
    return result
