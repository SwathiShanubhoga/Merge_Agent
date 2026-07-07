"""
Sales Data Merge Agent
----------------------
A simple Streamlit app that takes three files - Sales, Products, and Stores -
and merges them into one combined file using their common key columns.

How the merge logic works:
  Sales file usually contains IDs like product_id and store_id (not full names).
  Products file has product_id + product details (name, category, price).
  Stores file has store_id + store details (name, city, region).

  So we do two joins:
    Step 1: Sales + Products  -> joined on product_id
    Step 2: (Result) + Stores -> joined on store_id

This app lets the user upload any 3 files, auto-detects the common
column between each pair, and lets the user override the choice if needed.
"""

import streamlit as st
import pandas as pd

# ---------- Page setup ----------
st.set_page_config(page_title="Sales Merge Agent", layout="wide")
st.title("🔗 Sales Data Merge Agent")
st.write(
    "Upload your **Sales**, **Products**, and **Stores** files. "
    "This tool will automatically find the common key columns and merge them into one file."
)


# ---------- Helper function: read csv or excel ----------
def read_file(uploaded_file):
    """Reads a CSV or Excel file into a pandas DataFrame."""
    if uploaded_file is None:
        return None
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        st.error(f"Unsupported file type: {uploaded_file.name}")
        return None


def find_common_column(df1, df2):
    """Finds columns with the same name in both dataframes (candidate join keys)."""
    common = list(set(df1.columns) & set(df2.columns))
    return common


# ---------- File upload section ----------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1️⃣ Sales File")
    sales_file = st.file_uploader("Upload Sales file", type=["csv", "xlsx", "xls"], key="sales")

with col2:
    st.subheader("2️⃣ Products File")
    products_file = st.file_uploader("Upload Products file", type=["csv", "xlsx", "xls"], key="products")

with col3:
    st.subheader("3️⃣ Stores File")
    stores_file = st.file_uploader("Upload Stores file", type=["csv", "xlsx", "xls"], key="stores")

st.divider()

# ---------- Option to use sample data (for testing) ----------
use_sample = st.checkbox("No files handy? Use built-in sample data to try the app")

if use_sample:
    sales_df = pd.read_csv("sample_data/sales.csv")
    products_df = pd.read_csv("sample_data/products.csv")
    stores_df = pd.read_csv("sample_data/stores.csv")
else:
    sales_df = read_file(sales_file)
    products_df = read_file(products_file)
    stores_df = read_file(stores_file)

# ---------- Show previews ----------
if sales_df is not None:
    with st.expander("Preview: Sales data"):
        st.dataframe(sales_df.head())

if products_df is not None:
    with st.expander("Preview: Products data"):
        st.dataframe(products_df.head())

if stores_df is not None:
    with st.expander("Preview: Stores data"):
        st.dataframe(stores_df.head())

st.divider()

# ---------- Merge logic ----------
if sales_df is not None and products_df is not None and stores_df is not None:

    st.subheader("🔧 Merge Settings")

    # Auto-detect common key between Sales and Products
    sales_products_keys = find_common_column(sales_df, products_df)
    sales_stores_keys = find_common_column(sales_df, stores_df)

    colA, colB = st.columns(2)
    with colA:
        key1 = st.selectbox(
            "Common key between Sales & Products",
            options=sales_products_keys if sales_products_keys else sales_df.columns.tolist(),
        )
    with colB:
        key2 = st.selectbox(
            "Common key between Sales & Stores",
            options=sales_stores_keys if sales_stores_keys else sales_df.columns.tolist(),
        )

    if st.button("🚀 Merge Files", type="primary"):
        try:
            # Step 1: merge sales with products
            merged = pd.merge(sales_df, products_df, on=key1, how="left")

            # Step 2: merge result with stores
            merged = pd.merge(merged, stores_df, on=key2, how="left")

            st.success(f"Merged successfully! Final file has {merged.shape[0]} rows and {merged.shape[1]} columns.")
            st.dataframe(merged)

            # Download button
            csv_data = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Merged File (CSV)",
                data=csv_data,
                file_name="merged_sales_data.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Something went wrong while merging: {e}")

else:
    st.info("Upload all 3 files (or check the sample data box) to enable merging.")
