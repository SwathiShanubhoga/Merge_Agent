"""
BI Integration Module
---------------------
Provides BI-ready queries and exports for the Gold layer data.
Enables seamless integration with Tableau, Looker, Power BI, and other BI tools.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from gold import (
    prepare_gold_data,
    build_fct_sales_transactions,
    build_dim_customers,
    build_mtr_customer_metrics_daily,
    build_mtr_customer_lifetime_value,
)


BI_EXPORT_FOLDER = Path(
    r"C:\Users\sshanubhoga\Documents\ACCELERATE WITH AI\Export Files\BI"
)


def ensure_bi_export_folder():
    """Create BI export folder if it doesn't exist."""
    BI_EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    return BI_EXPORT_FOLDER


def get_highest_sales_by_product(gold_df, top_n=10):
    """
    Get highest sales transactions by product/customer.
    
    Args:
        gold_df: Gold layer dataframe
        top_n: Number of top sales to return
    
    Returns:
        DataFrame with top sales ranked by transaction amount
    """
    if gold_df.empty or "Total_Revenue" not in gold_df.columns:
        return pd.DataFrame()
    
    top_sales = (
        gold_df.nlargest(top_n, "Total_Revenue")[
            [
                "customer_name" if "customer_name" in gold_df.columns else "name",
                "Total_Revenue",
                "Transaction_Count",
                "Average_Transaction",
                "Quality_Score",
            ]
        ]
        .reset_index(drop=True)
    )
    
    top_sales.insert(0, "rank", range(1, len(top_sales) + 1))
    return top_sales


def get_sales_by_date_range(fct_sales, start_date=None, end_date=None):
    """
    Get sales transactions within a date range.
    
    Args:
        fct_sales: Fact sales table
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Filtered sales dataframe
    """
    if fct_sales.empty:
        return pd.DataFrame()
    
    df = fct_sales.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    
    if start_date:
        df = df[df["transaction_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["transaction_date"] <= pd.to_datetime(end_date)]
    
    return df


def get_top_performing_customers(gold_df, metric="Total_Revenue", top_n=10):
    """
    Get top performing customers by specified metric.
    
    Args:
        gold_df: Gold layer dataframe
        metric: Metric to rank by (Total_Revenue, Transaction_Count, etc.)
        top_n: Number of top customers
    
    Returns:
        DataFrame with top customers
    """
    if gold_df.empty or metric not in gold_df.columns:
        return pd.DataFrame()
    
    top_customers = gold_df.nlargest(top_n, metric).reset_index(drop=True)
    top_customers.insert(0, "rank", range(1, len(top_customers) + 1))
    
    return top_customers


def get_sales_summary_by_period(gold_df, group_by="month"):
    """
    Get sales summary grouped by time period.
    
    Args:
        gold_df: Gold layer dataframe
        group_by: 'month', 'quarter', or 'year'
    
    Returns:
        Aggregated sales by period
    """
    if gold_df.empty or "First_Seen" not in gold_df.columns:
        return pd.DataFrame()
    
    df = gold_df.copy()
    df["First_Seen"] = pd.to_datetime(df["First_Seen"], errors="coerce")
    
    if group_by == "month":
        df["period"] = df["First_Seen"].dt.to_period("M")
    elif group_by == "quarter":
        df["period"] = df["First_Seen"].dt.to_period("Q")
    else:  # year
        df["period"] = df["First_Seen"].dt.to_period("Y")
    
    summary = (
        df.groupby("period", as_index=False)
        .agg(
            Total_Revenue=("Total_Revenue", "sum"),
            Customer_Count=("customer_name" if "customer_name" in df.columns else "name", "nunique"),
            Avg_Revenue_Per_Customer=("Total_Revenue", "mean"),
        )
        .reset_index(drop=True)
    )
    
    summary["period"] = summary["period"].astype(str)
    return summary


def get_product_sales_breakdown(fct_sales):
    """
    Get sales breakdown by product/source file.
    
    Args:
        fct_sales: Fact sales table
    
    Returns:
        Sales aggregated by product
    """
    if fct_sales.empty or "source_file" not in fct_sales.columns:
        return pd.DataFrame()
    
    product_sales = (
        fct_sales.groupby("source_file", as_index=False)
        .agg(
            Total_Sales=("transaction_amount", "sum"),
            Transaction_Count=("transaction_id", "count"),
            Average_Transaction=("transaction_amount", "mean"),
            Valid_Records=("is_valid_record", "sum"),
        )
        .reset_index(drop=True)
    )
    
    product_sales.columns = [
        "Product",
        "Total_Sales",
        "Transaction_Count",
        "Average_Transaction",
        "Valid_Records",
    ]
    product_sales = product_sales.nlargest(100, "Total_Sales")
    product_sales.insert(0, "rank", range(1, len(product_sales) + 1))
    
    return product_sales


def export_to_json(dataframe, filename):
    """Export dataframe to JSON for BI integration."""
    ensure_bi_export_folder()
    filepath = BI_EXPORT_FOLDER / filename
    
    # Convert timestamps and handle serialization
    df = dataframe.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    
    df.to_json(filepath, orient="records", indent=2)
    return str(filepath)


def export_to_csv(dataframe, filename):
    """Export dataframe to CSV for BI integration."""
    ensure_bi_export_folder()
    filepath = BI_EXPORT_FOLDER / filename
    dataframe.to_csv(filepath, index=False)
    return str(filepath)


def export_to_parquet(dataframe, filename):
    """Export dataframe to Parquet for BI integration."""
    ensure_bi_export_folder()
    filepath = BI_EXPORT_FOLDER / filename
    dataframe.to_parquet(filepath, index=False)
    return str(filepath)


def generate_bi_dashboard_data(silver_df):
    """
    Generate comprehensive BI dashboard dataset from Silver layer.
    Returns all necessary tables and exports them for BI tools.
    
    Args:
        silver_df: Silver layer dataframe
    
    Returns:
        Dictionary with all BI-ready tables and export paths
    """
    ensure_bi_export_folder()
    
    # Build Gold layer tables
    gold_df = prepare_gold_data(silver_df)
    fct_sales = build_fct_sales_transactions(silver_df)
    dim_customers = build_dim_customers(silver_df)
    mtr_daily = build_mtr_customer_metrics_daily(silver_df, fct_sales)
    mtr_clv = build_mtr_customer_lifetime_value(fct_sales)
    
    # Generate BI queries\n    top_sales = get_highest_sales_by_product(gold_df, top_n=20)\n    top_customers = get_top_performing_customers(gold_df, metric=\"Total_Revenue\", top_n=15)\n    sales_by_period = get_sales_summary_by_period(gold_df, group_by=\"month\")\n    product_breakdown = get_product_sales_breakdown(fct_sales)\n    \n    # Export all tables\n    timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n    exports = {}\n    \n    # Export fact and dimension tables\n    exports[\"fact_sales\"] = export_to_parquet(\n        fct_sales, f\"fct_sales_transactions_{timestamp}.parquet\"\n    )\n    exports[\"dim_customers\"] = export_to_parquet(\n        dim_customers, f\"dim_customers_{timestamp}.parquet\"\n    )\n    exports[\"mtr_daily\"] = export_to_parquet(\n        mtr_daily, f\"mtr_customer_metrics_daily_{timestamp}.parquet\"\n    )\n    exports[\"mtr_clv\"] = export_to_parquet(\n        mtr_clv, f\"mtr_customer_lifetime_value_{timestamp}.parquet\"\n    )\n    \n    # Export BI queries\n    exports[\"top_sales\"] = export_to_json(\n        top_sales, f\"top_sales_products_{timestamp}.json\"\n    )\n    exports[\"top_customers\"] = export_to_csv(\n        top_customers, f\"top_customers_{timestamp}.csv\"\n    )\n    exports[\"sales_by_period\"] = export_to_csv(\n        sales_by_period, f\"sales_by_period_{timestamp}.csv\"\n    )\n    exports[\"product_breakdown\"] = export_to_json(\n        product_breakdown, f\"product_sales_breakdown_{timestamp}.json\"\n    )\n    \n    # Generate summary report\n    summary = {\n        \"Export_Date\": datetime.now().isoformat(),\n        \"Gold_Rows\": len(gold_df),\n        \"Fact_Sales_Rows\": len(fct_sales),\n        \"Customers\": len(dim_customers),\n        \"Daily_Metrics\": len(mtr_daily),\n        \"Top_Sales_Count\": len(top_sales),\n        \"Top_Customers_Count\": len(top_customers),\n        \"Total_Revenue\": float(gold_df[\"Total_Revenue\"].sum()),\n        \"Avg_Transaction\": float(gold_df[\"Average_Transaction\"].mean()),\n        \"Files_Exported\": len(exports),\n        \"Export_Location\": str(BI_EXPORT_FOLDER),\n        \"Exports\": exports,\n    }\n    \n    # Save summary as JSON\n    summary_path = BI_EXPORT_FOLDER / f\"bi_export_summary_{timestamp}.json\"\n    with open(summary_path, \"w\") as f:\n        json.dump(summary, f, indent=2, default=str)\n    summary[\"Summary_File\"] = str(summary_path)\n    \n    return summary\n\n\ndef create_bi_api_response(query_type, silver_df, params=None):\n    \"\"\"\n    Create API-ready response for BI tools.\n    \n    Args:\n        query_type: Type of query (top_sales, top_customers, sales_by_period, product_breakdown)\n        silver_df: Silver layer dataframe\n        params: Additional parameters (top_n, date_range, etc.)\n    \n    Returns:\n        Dictionary ready for JSON API response\n    \"\"\"\n    if params is None:\n        params = {}\n    \n    gold_df = prepare_gold_data(silver_df)\n    fct_sales = build_fct_sales_transactions(silver_df)\n    \n    top_n = params.get(\"top_n\", 10)\n    \n    if query_type == \"top_sales\":\n        data = get_highest_sales_by_product(gold_df, top_n=top_n)\n    elif query_type == \"top_customers\":\n        metric = params.get(\"metric\", \"Total_Revenue\")\n        data = get_top_performing_customers(gold_df, metric=metric, top_n=top_n)\n    elif query_type == \"sales_by_period\":\n        period = params.get(\"period\", \"month\")\n        data = get_sales_summary_by_period(gold_df, group_by=period)\n    elif query_type == \"product_breakdown\":\n        data = get_product_sales_breakdown(fct_sales)\n    else:\n        data = pd.DataFrame()\n    \n    response = {\n        \"status\": \"success\",\n        \"query_type\": query_type,\n        \"timestamp\": datetime.now().isoformat(),\n        \"row_count\": len(data),\n        \"data\": data.to_dict(orient=\"records\") if not data.empty else [],\n    }\n    \n    return response
