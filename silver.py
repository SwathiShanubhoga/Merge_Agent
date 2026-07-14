import re
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os


# Silver export folder
SILVER_EXPORT_FOLDER = Path(r"C:\Users\sshanubhoga\Documents\ACCELERATE WITH AI\Export Files\Silver")


def ensure_silver_export_folder():
    """Create Silver export folder if it doesn't exist."""
    try:
        SILVER_EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating Silver export folder: {e}")
        return False


def export_silver_data(silver_df, source_files=None):
    """Export Silver layer data to CSV files."""
    if not ensure_silver_export_folder():
        return {"status": "failed", "error": "Could not create export folder"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_status = {}
    saved_files = []
    
    try:
        # Export merged Silver data
        merged_filename = f"silver_merged_{timestamp}.csv"
        merged_filepath = SILVER_EXPORT_FOLDER / merged_filename
        silver_df.to_csv(merged_filepath, index=False)
        saved_files.append(str(merged_filepath))
        export_status["merged"] = f"✓ {merged_filename}"
        print(f"[SILVER] Exported merged: {merged_filepath}")
        
        # Export valid records only
        valid_df = silver_df[silver_df["is_valid_record"] == True]
        if len(valid_df) > 0:
            valid_filename = f"silver_valid_records_{timestamp}.csv"
            valid_filepath = SILVER_EXPORT_FOLDER / valid_filename
            valid_df.to_csv(valid_filepath, index=False)
            saved_files.append(str(valid_filepath))
            export_status["valid_records"] = f"✓ {valid_filename}"
            print(f"[SILVER] Exported valid records: {valid_filepath}")
        
        # Export invalid records for review
        invalid_df = silver_df[silver_df["is_valid_record"] == False]
        if len(invalid_df) > 0:
            invalid_filename = f"silver_invalid_records_{timestamp}.csv"
            invalid_filepath = SILVER_EXPORT_FOLDER / invalid_filename
            invalid_df.to_csv(invalid_filepath, index=False)
            saved_files.append(str(invalid_filepath))
            export_status["invalid_records"] = f"✓ {invalid_filename}"
            print(f"[SILVER] Exported invalid records: {invalid_filepath}")
        
        # Export data quality summary
        quality_summary = {
            "Export_Timestamp": datetime.now().isoformat(),
            "Total_Records": len(silver_df),
            "Valid_Records": len(valid_df),
            "Invalid_Records": len(invalid_df),
            "Valid_Percentage": round(len(valid_df) / len(silver_df) * 100, 2) if len(silver_df) > 0 else 0,
            "Quality_Issues": silver_df[silver_df["is_valid_record"] == False]["error_reason"].unique().tolist() if len(invalid_df) > 0 else []
        }
        
        summary_filename = f"silver_quality_summary_{timestamp}.csv"
        summary_filepath = SILVER_EXPORT_FOLDER / summary_filename
        pd.DataFrame([quality_summary]).to_csv(summary_filepath, index=False)
        saved_files.append(str(summary_filepath))
        export_status["quality_summary"] = f"✓ {summary_filename}"
        print(f"[SILVER] Exported quality summary: {summary_filepath}")
        
        return {
            "status": "success",
            "files_exported": len(saved_files),
            "saved_files": saved_files,
            "export_status": export_status,
            "quality_summary": quality_summary,
            "export_location": str(SILVER_EXPORT_FOLDER)
        }
    
    except Exception as e:
        print(f"[SILVER] Export error: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "files_exported": len(saved_files),
            "saved_files": saved_files
        }


def validate_phone_number(phone):
    """Validate phone number format: XXX-XXX-XXXX or XXXXXXXXXX."""
    if pd.isna(phone) or phone == "":
        return True  # Allow empty, will be flagged separately
    phone_str = str(phone).strip()
    pattern = r"^(\d{10}|\d{3}-\d{3}-\d{4}|\+1\d{10})$"
    return bool(re.match(pattern, phone_str))


def validate_email(email):
    """Validate email format."""
    if pd.isna(email) or email == "":
        return True  # Allow empty, will be flagged separately
    email_str = str(email).strip()
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email_str))


def validate_revenue(amount):
    """Validate revenue is non-negative."""
    if pd.isna(amount):
        return True  # Will be handled by null handling
    return float(amount) >= 0


def validate_date_format(date_str):
    """Validate date is in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format."""
    if pd.isna(date_str) or date_str == "":
        return True
    try:
        pd.to_datetime(str(date_str))
        return True
    except:
        return False


def prepare_silver_data(bronze_df):
    """Clean, validate, and enrich Bronze data for the Silver layer."""
    silver_df = bronze_df.copy()
    
    # Initialize quality flags
    silver_df["is_valid_record"] = True
    silver_df["error_reason"] = ""
    
    # Identify primary key columns (common patterns)
    primary_key_cols = [col for col in silver_df.columns if "id" in col.lower() or col.lower() == "code"]
    if not primary_key_cols and "name" in silver_df.columns:
        primary_key_cols = ["name"]
    
    # ========== STEP 1: Handle Null Values ==========
    # Check for nulls in primary key columns
    for pk_col in primary_key_cols:
        if pk_col in silver_df.columns:
            null_mask = silver_df[pk_col].isna()
            silver_df.loc[null_mask, "is_valid_record"] = False
            silver_df.loc[null_mask, "error_reason"] += f"NULL in primary key '{pk_col}'; "
            # Drop rows with nulls in primary keys
            silver_df = silver_df[~null_mask].reset_index(drop=True)
    
    # Impute nulls in secondary columns (amount, quantity, etc.)
    numeric_cols = silver_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in primary_key_cols:
            null_mask = silver_df[col].isna()
            if null_mask.any():
                median_val = silver_df[col].median()
                silver_df.loc[null_mask, col] = median_val if not pd.isna(median_val) else 0
                # Mark records with imputed values
                silver_df.loc[null_mask, "error_reason"] += f"Imputed {col}; "
    
    # ========== STEP 2: Type Casting and Standardization ==========
    # Standardize text columns
    text_cols = ["name", "Name", "product_name", "store_name", "category"]
    for col in text_cols:
        if col in silver_df.columns:
            silver_df[col] = silver_df[col].fillna("").astype(str).str.strip().str.lower()
    
    # Cast numeric columns (amount, price, quantity, revenue)
    numeric_target_cols = ["amount", "price", "quantity", "revenue", "sales", "cost"]
    for col in numeric_target_cols:
        if col in silver_df.columns:
            try:
                silver_df[col] = pd.to_numeric(silver_df[col], errors="coerce")
            except:
                pass
    
    # Cast date columns
    date_cols = [col for col in silver_df.columns if "date" in col.lower() or "time" in col.lower()]
    for col in date_cols:
        if col in silver_df.columns and col not in ["_ingestion_timestamp"]:
            try:
                silver_df[col] = pd.to_datetime(silver_df[col], errors="coerce")
            except:
                pass
    
    # ========== STEP 3: Business Rules Validation ==========
    # RULE 1: No negative revenue/amount
    for revenue_col in ["amount", "price", "revenue", "sales"]:
        if revenue_col in silver_df.columns:
            negative_mask = (silver_df[revenue_col] < 0) & (silver_df[revenue_col].notna())
            silver_df.loc[negative_mask, "is_valid_record"] = False
            silver_df.loc[negative_mask, "error_reason"] += f"Negative {revenue_col}; "
    
    # RULE 2: Phone number validation (if phone column exists)
    if "phone" in silver_df.columns:
        phone_invalid = ~silver_df["phone"].apply(validate_phone_number)
        silver_df.loc[phone_invalid, "is_valid_record"] = False
        silver_df.loc[phone_invalid, "error_reason"] += "Invalid phone format; "
    
    # RULE 3: Email validation (if email column exists)
    if "email" in silver_df.columns:
        email_invalid = ~silver_df["email"].apply(validate_email)
        silver_df.loc[email_invalid, "is_valid_record"] = False
        silver_df.loc[email_invalid, "error_reason"] += "Invalid email format; "
    
    # ========== STEP 4: Deduplication ==========
    # Deduplicate based on primary key + ingestion timestamp
    dedup_cols = primary_key_cols + ["_ingestion_timestamp"] if "_ingestion_timestamp" in silver_df.columns else primary_key_cols
    if dedup_cols:
        duplicate_mask = silver_df.duplicated(subset=dedup_cols, keep="first")
        silver_df.loc[duplicate_mask, "error_reason"] += "Duplicate record; "
        silver_df = silver_df[~duplicate_mask].reset_index(drop=True)
    
    # ========== STEP 5: Schema Evolution ==========
    # Ensure standard Silver layer columns exist
    required_silver_cols = [
        "is_valid_record",
        "error_reason",
        "status",
        "layer",
        "_source_system",
        "_ingestion_timestamp",
    ]
    for col in required_silver_cols:
        if col not in silver_df.columns:
            if col == "is_valid_record":
                silver_df[col] = True
            elif col == "error_reason":
                silver_df[col] = ""
            elif col == "status":
                silver_df[col] = "validated"
            elif col == "layer":
                silver_df[col] = "silver"
            else:
                silver_df[col] = ""
    
    # Update status and layer for all records
    silver_df["status"] = "validated"
    silver_df["layer"] = "silver"
    
    # Trim error_reason to clean up trailing semicolons
    silver_df["error_reason"] = silver_df["error_reason"].str.rstrip("; ")
    
    # Export Silver data to folder
    export_summary = export_silver_data(silver_df)
    
    return silver_df.reset_index(drop=True), export_summary
