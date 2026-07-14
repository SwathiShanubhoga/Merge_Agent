import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import os


# Gold export folder
GOLD_EXPORT_FOLDER = Path(r"C:\Users\sshanubhoga\Documents\ACCELERATE WITH AI\Export Files\Gold")


def ensure_gold_export_folder():
    """Create Gold export folder if it doesn't exist."""
    try:
        GOLD_EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating Gold export folder: {e}")
        return False


def export_gold_data(gold_df):
    """Export Gold layer data to CSV files."""
    if not ensure_gold_export_folder():
        return {"status": "failed", "error": "Could not create export folder"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_status = {}
    saved_files = []
    
    try:
        # Export Gold metrics
        gold_filename = f"gold_metrics_{timestamp}.csv"
        gold_filepath = GOLD_EXPORT_FOLDER / gold_filename
        gold_df.to_csv(gold_filepath, index=False)
        saved_files.append(str(gold_filepath))
        export_status["gold_metrics"] = f"✓ {gold_filename}"
        print(f"[GOLD] Exported metrics: {gold_filepath}")
        
        # Export summary statistics
        if not gold_df.empty:
            summary_stats = {
                "Export_Timestamp": datetime.now().isoformat(),
                "Total_Entities": len(gold_df),
                "Total_Revenue": gold_df["Total_Revenue"].sum() if "Total_Revenue" in gold_df.columns else 0,
                "Average_Transaction": gold_df["Average_Transaction"].mean() if "Average_Transaction" in gold_df.columns else 0,
                "Total_Transactions": gold_df["Transaction_Count"].sum() if "Transaction_Count" in gold_df.columns else 0,
                "Average_Quality_Score": gold_df["Quality_Score"].mean() if "Quality_Score" in gold_df.columns else 0,
            }
            
            summary_filename = f"gold_summary_{timestamp}.csv"
            summary_filepath = GOLD_EXPORT_FOLDER / summary_filename
            pd.DataFrame([summary_stats]).to_csv(summary_filepath, index=False)
            saved_files.append(str(summary_filepath))
            export_status["summary"] = f"✓ {summary_filename}"
            print(f"[GOLD] Exported summary: {summary_filepath}")
        
        return {
            "status": "success",
            "files_exported": len(saved_files),
            "saved_files": saved_files,
            "export_status": export_status,
            "export_location": str(GOLD_EXPORT_FOLDER)
        }
    
    except Exception as e:
        print(f"[GOLD] Export error: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "files_exported": len(saved_files),
            "saved_files": saved_files
        }


# Helper function to find columns by pattern
def find_column(df, patterns):
    """Find a column in dataframe matching any of the patterns (case-insensitive)."""
    patterns = [p.lower() for p in patterns]
    for col in df.columns:
        if col.lower() in patterns or any(p in col.lower() for p in patterns):
            return col
    return None


DEFAULT_SEMANTIC_LAYER_YAML = """
# Semantic Layer Definition (LookML / dbt Semantic Layer format)
views:
  - name: fct_sales_transactions
    sql_table_name: gold.fct_sales_transactions
    dimensions:
      - name: transaction_id
        primary_key: true
        type: string
        sql: ${TABLE}.transaction_id
      - name: entity_id
        type: string
        sql: ${TABLE}.entity_id
      - name: transaction_date
        type: date
        sql: ${TABLE}.transaction_date
    measures:
      - name: transaction_amount_sum
        type: sum
        sql: ${TABLE}.transaction_amount
      - name: transaction_count
        type: count
      - name: average_transaction_amount
        type: average
        sql: ${TABLE}.transaction_amount

  - name: dim_entities
    sql_table_name: gold.dim_entities
    dimensions:
      - name: entity_id
        primary_key: true
        type: string
        sql: ${TABLE}.entity_id
      - name: entity_acquisition_date
        type: date
        sql: ${TABLE}.entity_acquisition_date
    measures:
      - name: entity_count
        type: count

  - name: mtr_daily_metrics
    sql_table_name: gold.mtr_daily_metrics
    dimensions:
      - name: metric_date
        primary_key: true
        type: date
        sql: ${TABLE}.metric_date
    measures:
      - name: daily_active_entities
        type: sum
        sql: ${TABLE}.daily_active_entities
      - name: daily_revenue
        type: sum
        sql: ${TABLE}.daily_revenue
"""


def build_dim_entities(silver_df, entity_col):
    """
    Build Dimension table: dim_entities
    Uses the identified entity column (customer, store, product, etc.)
    """
    if entity_col not in silver_df.columns or silver_df.empty:
        return pd.DataFrame()
    
    dim_entities = silver_df.groupby(entity_col, as_index=False).agg(
        Entity_ID=(
            entity_col,
            lambda x: f"ENT_{hash(x.iloc[0]) % 100000:05d}",
        ),
        Entity_Name=(entity_col, "first"),
        Entity_Acquisition_Date=(
            "_ingestion_timestamp",
            lambda x: pd.to_datetime(x.iloc[0]).date() if x.notna().any() else None,
        ),
        Total_Records=(entity_col, "count"),
        First_Seen=("_ingestion_timestamp", "min"),
        Last_Seen=("_ingestion_timestamp", "max"),
    ).drop_duplicates(subset=["Entity_ID"])
    
    return dim_entities.reset_index(drop=True)


def build_fct_sales_transactions(silver_df, entity_col):
    """
    Build Fact table: fct_sales_transactions
    Uses the identified entity column for grouping
    """
    if silver_df.empty:
        return pd.DataFrame()
    
    fct_sales = silver_df.copy()
    
    # Add transaction-level identifiers
    fct_sales["Transaction_ID"] = (
        fct_sales.index.astype(str) + "_" + fct_sales["_ingestion_timestamp"].astype(str)
    ).apply(lambda x: f"TXN_{hash(x) % 1000000:06d}")
    
    # Extract/create transaction date
    date_col = find_column(fct_sales, ["date", "time"])
    if date_col:
        fct_sales["Transaction_Date"] = pd.to_datetime(
            fct_sales[date_col], errors="coerce"
        ).dt.date
    else:
        fct_sales["Transaction_Date"] = pd.to_datetime(
            fct_sales["_ingestion_timestamp"], errors="coerce"
        ).dt.date
    
    # Use appropriate amount column
    amount_col = find_column(fct_sales, ["amount", "price", "revenue", "sales", "total"])
    if amount_col:
        fct_sales["Transaction_Amount"] = pd.to_numeric(
            fct_sales[amount_col], errors="coerce"
        ).fillna(0)
    else:
        fct_sales["Transaction_Amount"] = 1  # Default value if no amount found
    
    # Get entity value or create a generic one
    fct_sales["Entity_ID"] = fct_sales[entity_col].fillna("UNKNOWN").astype(str)
    
    # Business metrics
    fct_sales["Is_Valid_Record"] = fct_sales.get("is_valid_record", True)
    fct_sales["Quality_Flag"] = fct_sales.get("error_reason", "")
    
    # Create Gold columns
    fct_sales_gold = pd.DataFrame({
        "transaction_id": fct_sales["Transaction_ID"],
        "entity_id": fct_sales["Entity_ID"],
        "transaction_date": fct_sales["Transaction_Date"],
        "transaction_amount": fct_sales["Transaction_Amount"],
        "is_valid_record": fct_sales["Is_Valid_Record"],
        "quality_flag": fct_sales["Quality_Flag"],
        "ingestion_timestamp": fct_sales["_ingestion_timestamp"],
        "source_file": fct_sales.get("source_file", "unknown"),
    })
    
    return fct_sales_gold.reset_index(drop=True)


def build_mtr_daily_metrics(fct_sales):
    """
    Build Metrics table: mtr_daily_metrics
    Aggregates Daily Active Entities and Daily Revenue
    """
    if fct_sales.empty or "transaction_date" not in fct_sales.columns:
        return pd.DataFrame()
    
    # Group by date
    daily_metrics = fct_sales.groupby("transaction_date", as_index=False).agg(
        Daily_Active_Entities=("entity_id", "nunique"),
        Daily_Revenue=("transaction_amount", "sum"),
        Transaction_Count=("transaction_id", "count"),
        Valid_Records=("is_valid_record", "sum"),
    )
    
    daily_metrics.columns = [
        "metric_date",
        "daily_active_entities",
        "daily_revenue",
        "transaction_count",
        "valid_records",
    ]
    
    # Calculate metrics
    daily_metrics["average_transaction_value"] = (
        daily_metrics["daily_revenue"] / daily_metrics["transaction_count"]
    ).fillna(0)
    
    # Calculate moving average for trend
    daily_metrics["daily_revenue_7day_avg"] = (
        daily_metrics["daily_revenue"].rolling(window=7, min_periods=1).mean()
    )
    
    return daily_metrics.reset_index(drop=True)


def build_mtr_entity_lifetime_value(fct_sales):
    """
    Build Metrics table: mtr_entity_lifetime_value
    Aggregates CLV per entity with acquisition cost analysis
    """
    if fct_sales.empty or "entity_id" not in fct_sales.columns:
        return pd.DataFrame()
    
    clv_metrics = fct_sales.groupby("entity_id", as_index=False).agg(
        Total_Transactions=("transaction_id", "count"),
        Entity_Lifetime_Value=("transaction_amount", "sum"),
        Average_Transaction_Value=("transaction_amount", "mean"),
        First_Transaction_Date=("transaction_date", "min"),
        Last_Transaction_Date=("transaction_date", "max"),
    ).reset_index(drop=True)
    
    clv_metrics.columns = [
        "entity_id",
        "total_transactions",
        "entity_lifetime_value",
        "average_transaction_value",
        "first_transaction_date",
        "last_transaction_date",
    ]
    
    # Calculate entity tenure in days
    clv_metrics["entity_lifetime_value"] = (
        clv_metrics["entity_lifetime_value"].fillna(0)
    )
    clv_metrics["entity_tenure_days"] = (
        pd.to_datetime(clv_metrics["last_transaction_date"])
        - pd.to_datetime(clv_metrics["first_transaction_date"])
    ).dt.days.fillna(0)
    
    # Estimate acquisition cost (assume 10% of CLV for demo)
    clv_metrics["entity_acquisition_cost"] = (
        clv_metrics["entity_lifetime_value"] * 0.1
    )
    
    return clv_metrics


def prepare_gold_data(silver_df):
    """
    Prepare comprehensive Gold layer with Fact and Dimension tables.
    Dynamically detects entity columns and aggregates accordingly.
    """
    if silver_df.empty:
        return pd.DataFrame(), {"status": "failed", "error": "Empty Silver dataframe"}
    
    # Detect entity column (customer, store, product, etc.)
    entity_col = find_column(silver_df, ["name", "customer_name", "store_id", "product_id", "store", "product"])
    
    if not entity_col:
        # Use first ID-like column or first column as entity
        id_cols = [col for col in silver_df.columns if "id" in col.lower()]
        entity_col = id_cols[0] if id_cols else silver_df.columns[0]
    
    print(f"[GOLD] Using entity column: {entity_col}")
    
    # Build dimension and fact tables
    dim_entities = build_dim_entities(silver_df, entity_col)
    fct_sales = build_fct_sales_transactions(silver_df, entity_col)
    
    # Build metric tables
    mtr_daily = build_mtr_daily_metrics(fct_sales)
    mtr_clv = build_mtr_entity_lifetime_value(fct_sales)
    
    # Create a unified gold view for business metrics
    if not fct_sales.empty:
        gold_df = (
            fct_sales.groupby("entity_id", as_index=False)
            .agg(
                Total_Revenue=("transaction_amount", "sum"),
                Transaction_Count=("transaction_id", "count"),
                Average_Transaction=("transaction_amount", "mean"),
                First_Seen=("transaction_date", "min"),
                Last_Seen=("transaction_date", "max"),
                Quality_Score=("is_valid_record", "mean"),
            )
            .reset_index(drop=True)
        )
    else:
        gold_df = pd.DataFrame()
    
    # Add Gold layer markers
    if not gold_df.empty:
        gold_df["layer"] = "gold"
        gold_df["timestamp"] = datetime.now()
        
        # Export Gold data
        export_summary = export_gold_data(gold_df)
    else:
        export_summary = {"status": "failed", "error": "No Gold data generated"}
    
    return gold_df, export_summary


def get_semantic_layer_definition():
    """Return the semantic layer YAML definition for BI tools."""
    return DEFAULT_SEMANTIC_LAYER_YAML
