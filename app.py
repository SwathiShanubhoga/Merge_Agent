"""
Medallion Data Pipeline
----------------------
A Streamlit app that lets the user upload files, then move them through
Bronze, Silver, and Gold layers after explicit confirmation.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from bronze import prepare_bronze_data
from silver import prepare_silver_data
from gold import prepare_gold_data

# ---------- Page setup ----------
st.set_page_config(page_title="Medallion Pipeline", layout="wide")
st.title("🪙 Medallion Architecture Workflow")
st.write(
    "Upload one or more files, confirm each layer, and watch the data move from "
    "Bronze → Silver → Gold."
)


# ---------- Helper functions ----------
def read_file(uploaded_file):
    """Reads a CSV or Excel file into a pandas DataFrame."""
    if uploaded_file is None:
        return None

    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    st.error(f"Unsupported file type: {uploaded_file.name}")
    return None


def build_sample_data():
    """Returns built-in sample files as a list of (name, dataframe) tuples."""
    return [
        ("sales.csv", pd.read_csv("sample_data/sales.csv")),
        ("products.csv", pd.read_csv("sample_data/products.csv")),
        ("stores.csv", pd.read_csv("sample_data/stores.csv")),
    ]


# ---------- Session state for staged workflow ----------
if "stage" not in st.session_state:
    st.session_state.stage = "upload"
if "bronze_df" not in st.session_state:
    st.session_state.bronze_df = None
if "bronze_summary" not in st.session_state:
    st.session_state.bronze_summary = None
if "silver_df" not in st.session_state:
    st.session_state.silver_df = None
if "silver_summary" not in st.session_state:
    st.session_state.silver_summary = None
if "gold_df" not in st.session_state:
    st.session_state.gold_df = None
if "gold_summary" not in st.session_state:
    st.session_state.gold_summary = None


# ---------- File upload section ----------
uploaded_files = st.file_uploader(
    "Upload files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    key="multi_upload",
)

use_sample = st.checkbox("No files handy? Use built-in sample data to try the app")

if use_sample:
    dataframes = build_sample_data()
else:
    dataframes = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            df = read_file(uploaded_file)
            if df is not None:
                dataframes.append((uploaded_file.name, df))

if dataframes:
    st.subheader("Uploaded files")
    for file_name, df in dataframes:
        with st.expander(f"Preview: {file_name}", expanded=False):
            st.dataframe(df.head())
else:
    st.info("Upload one or more files (or check the sample data box) to begin the pipeline.")

st.divider()

# ---------- Pipeline progress / stage display ----------
step_names = ["Bronze", "Silver", "Gold"]
stage_index = {"upload": 0, "bronze": 1, "silver": 2, "gold": 3}
current_step = stage_index[st.session_state.stage]

st.subheader("Pipeline progress")
st.progress(current_step / 3)

cols = st.columns(3)
for i, layer in enumerate(step_names):
    with cols[i]:
        if i + 1 < current_step:
            st.success(f"{i + 1}. {layer} ✅")
        elif i + 1 == current_step:
            st.info(f"{i + 1}. {layer} ▶")
        else:
            st.caption(f"{i + 1}. {layer}")

st.divider()

# ---------- Bronze layer ----------
st.subheader("Bronze Layer (Raw)")
st.write(
    "This is the landing zone for ingested data. It keeps the original structure "
    "and records the source file for traceability."
)

if dataframes and st.button("Confirm Bronze Layer", type="primary"):
    bronze_result = prepare_bronze_data(dataframes)

    if isinstance(bronze_result, tuple) and len(bronze_result) == 2:
        bronze_df, bronze_summary = bronze_result
    else:
        bronze_df = bronze_result
        bronze_summary = {
            "files_ingested": 1 if not bronze_df.empty else 0,
            "rows_ingested": int(len(bronze_df)),
            "columns_ingested": int(len(bronze_df.columns)),
            "files": [],
        }

    st.session_state.bronze_df = bronze_df
    st.session_state.bronze_summary = bronze_summary
    st.session_state.stage = "bronze"
    st.session_state.silver_df = None
    st.session_state.gold_df = None

if st.session_state.bronze_df is not None:
    st.success("Bronze layer confirmed")
    with st.expander("Bronze preview", expanded=True):
        st.dataframe(st.session_state.bronze_df.head())

    if st.session_state.get("bronze_summary"):
        st.subheader("Bronze ingestion summary")
        st.metric("Files ingested", st.session_state.bronze_summary["files_ingested"])
        st.metric("Rows ingested", st.session_state.bronze_summary["rows_ingested"])
        
        # Display export status
        export_status = st.session_state.bronze_summary.get("export_status", {})
        if export_status.get("success"):
            st.success(f"✅ Export successful: {export_status.get('message', 'Files saved')}")
        else:
            if export_status.get("message"):
                st.warning(f"⚠️ Export status: {export_status['message']}")
        
        # Display export folder
        if st.session_state.bronze_summary.get("export_folder"):
            st.info(
                f"📁 **Bronze export folder:**\n\n`{st.session_state.bronze_summary['export_folder']}`"
            )
        
        # Display individually saved files
        if export_status.get("saved_files"):
            st.subheader("Ingested files")
            for saved_file in export_status["saved_files"]:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.code(f"{saved_file['saved_as']}", language="text")
                with col2:
                    st.caption(f"{saved_file['rows']} rows | {saved_file['size_bytes']:,} bytes")
        
        # Display merged file
        if export_status.get("merged_file"):
            st.subheader("Merged Bronze file")
            merged = export_status["merged_file"]
            st.code(Path(merged["path"]).name, language="text")
            st.caption(f"{merged['size_bytes']:,} bytes")
        
        with st.expander("Full export details (JSON)"):
            st.json(st.session_state.bronze_summary)

st.divider()

# ---------- Silver layer ----------
st.subheader("Silver Layer (Enriched)")
st.write(
    "This layer cleans, validates, and standardizes the data for downstream use."
)

if st.session_state.bronze_df is not None and st.button("Confirm Silver Layer", type="primary"):
    silver_result = prepare_silver_data(st.session_state.bronze_df)
    
    if isinstance(silver_result, tuple) and len(silver_result) == 2:
        silver_df, silver_summary = silver_result
    else:
        silver_df = silver_result
        silver_summary = {
            "status": "success",
            "files_exported": 0,
            "quality_summary": {}
        }
    
    st.session_state.silver_df = silver_df
    st.session_state.silver_summary = silver_summary
    st.session_state.stage = "silver"
    st.session_state.gold_df = None

if st.session_state.silver_df is not None:
    st.success("Silver layer confirmed")
    with st.expander("Silver preview", expanded=True):
        st.dataframe(st.session_state.silver_df.head())
    
    if st.session_state.get("silver_summary"):
        st.subheader("Silver data quality summary")
        
        # Get quality metrics
        summary = st.session_state.silver_summary.get("quality_summary", {})
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", summary.get("Total_Records", 0))
            with col2:
                st.metric("Valid Records", summary.get("Valid_Records", 0))
            with col3:
                st.metric("Invalid Records", summary.get("Invalid_Records", 0))
            with col4:
                st.metric("Quality Score", f"{summary.get('Valid_Percentage', 0):.1f}%")
        
        # Display export status
        export_status = st.session_state.silver_summary.get("status", "")
        if export_status == "success":
            st.success(f"✅ Silver files exported successfully")
        
        # Display export folder
        export_location = st.session_state.silver_summary.get("export_location", "")
        if export_location:
            st.info(f"📁 **Silver export folder:**\n\n`{export_location}`")
        
        # Display exported files
        saved_files = st.session_state.silver_summary.get("saved_files", [])
        if saved_files:
            st.subheader("Exported Silver files")
            for saved_file in saved_files:
                st.code(Path(saved_file).name, language="text")
        
        with st.expander("Full export details (JSON)"):
            st.json(st.session_state.silver_summary)

st.divider()

# ---------- Gold layer ----------
st.subheader("Gold Layer (Curated)")
st.write(
    "This layer creates curated, business-ready outputs such as summaries or KPIs."
)

if st.session_state.silver_df is not None and st.button("Confirm Gold Layer", type="primary"):
    gold_result = prepare_gold_data(st.session_state.silver_df)
    
    if isinstance(gold_result, tuple) and len(gold_result) == 2:
        gold_df, gold_summary = gold_result
    else:
        gold_df = gold_result
        gold_summary = {
            "status": "success",
            "files_exported": 0,
            "export_status": {}
        }
    
    st.session_state.gold_df = gold_df
    st.session_state.gold_summary = gold_summary
    st.session_state.stage = "gold"

if st.session_state.gold_df is not None:
    st.success("Gold layer confirmed")
    
    # Display Gold business metrics
    if not st.session_state.gold_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            total_revenue = st.session_state.gold_df["Total_Revenue"].sum()
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        with col2:
            total_transactions = st.session_state.gold_df["Transaction_Count"].sum()
            st.metric("Total Transactions", f"{total_transactions:,.0f}")
        with col3:
            avg_transaction = st.session_state.gold_df["Average_Transaction"].mean()
            st.metric("Average Transaction Value", f"${avg_transaction:,.2f}")
    
    # Display semantic layer definition
    from gold import get_semantic_layer_definition
    with st.expander("📊 Semantic Layer Definition (LookML/dbt)", expanded=False):
        semantic_yaml = get_semantic_layer_definition()
        st.code(semantic_yaml, language="yaml")
    
    # Display data preview
    with st.expander("Gold preview", expanded=True):
        st.dataframe(st.session_state.gold_df.head())

    csv_data = st.session_state.gold_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Gold Layer CSV",
        data=csv_data,
        file_name="gold_layer.csv",
        mime="text/csv",
    )
