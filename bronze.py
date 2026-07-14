from datetime import datetime, timezone
from pathlib import Path
import os

import pandas as pd

# Define the Bronze export folder
BRONZE_EXPORT_FOLDER = Path(
    r"C:\Users\sshanubhoga\Documents\ACCELERATE WITH AI\Export Files\Bronze"
)


def prepare_bronze_data(uploaded_files, source_system="uploaded_files"):
    """Ingest uploaded files into the Bronze layer without dropping rows or columns."""
    rows = []
    summaries = []
    ingestion_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    export_status = {"success": False, "message": "", "saved_files": [], "export_folder": str(BRONZE_EXPORT_FOLDER)}
    
    # Create Bronze export folder if it doesn't exist
    try:
        BRONZE_EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"INFO: Export folder ready at {BRONZE_EXPORT_FOLDER}")
    except Exception as e:
        export_status["message"] = f"Error creating export folder: {str(e)}"
        print(f"ERROR: {export_status['message']}")

    # Save each file individually to Bronze
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for file_name, df in uploaded_files:
        bronze_df = df.copy()
        bronze_df["_ingestion_timestamp"] = ingestion_timestamp
        bronze_df["_source_system"] = source_system
        bronze_df["source_file"] = file_name
        bronze_df["layer"] = "bronze"
        rows.append(bronze_df)

        # Save individual file to Bronze folder
        try:
            file_base_name = Path(file_name).stem  # Get filename without extension
            individual_file_path = BRONZE_EXPORT_FOLDER / f"{file_base_name}_{timestamp_str}.csv"
            bronze_df.to_csv(individual_file_path, index=False)
            
            if individual_file_path.exists():
                file_size = os.path.getsize(individual_file_path)
                export_status["saved_files"].append({
                    "original_name": file_name,
                    "saved_as": individual_file_path.name,
                    "path": str(individual_file_path),
                    "rows": int(len(bronze_df)),
                    "size_bytes": file_size,
                })
                print(f"SUCCESS: Saved {file_name} to {individual_file_path} ({file_size} bytes)")
            else:
                print(f"ERROR: Failed to create file for {file_name}")
        except Exception as e:
            print(f"ERROR saving {file_name}: {str(e)}")

        summaries.append(
            {
                "file_name": file_name,
                "rows_ingested": int(len(bronze_df)),
                "columns_ingested": int(len(bronze_df.columns)),
                "schema": list(bronze_df.columns),
                "ingestion_timestamp": ingestion_timestamp,
                "source_system": source_system,
            }
        )

    if not rows:
        empty_df = pd.DataFrame(
            columns=["source_file", "layer", "_ingestion_timestamp", "_source_system"]
        )
        return empty_df, {
            "files_ingested": 0,
            "rows_ingested": 0,
            "columns_ingested": 4,
            "files": [],
            "export_path": str(BRONZE_EXPORT_FOLDER),
            "export_status": export_status,
        }

    bronze_df = pd.concat(rows, ignore_index=True)
    
    # Save merged Bronze file for reference
    try:
        merged_file_path = BRONZE_EXPORT_FOLDER / f"bronze_merged_{timestamp_str}.csv"
        
        if not BRONZE_EXPORT_FOLDER.exists():
            raise FileNotFoundError(f"Export folder does not exist: {BRONZE_EXPORT_FOLDER}")
        
        bronze_df.to_csv(merged_file_path, index=False)
        
        if merged_file_path.exists():
            file_size = os.path.getsize(merged_file_path)
            export_status["success"] = True
            export_status["message"] = f"All {len(export_status['saved_files'])} files ingested and saved"
            export_status["merged_file"] = {
                "path": str(merged_file_path),
                "size_bytes": file_size,
            }
            print(f"SUCCESS: Merged Bronze file exported to {merged_file_path} ({file_size} bytes)")
        else:
            print(f"ERROR: Merged file was not created at {merged_file_path}")
    except Exception as e:
        export_status["message"] = f"Error saving merged Bronze file: {str(e)}"
        print(f"ERROR: {export_status['message']}")
    
    summary = {
        "files_ingested": len(summaries),
        "rows_ingested": int(len(bronze_df)),
        "columns_ingested": int(len(bronze_df.columns)),
        "files": summaries,
        "export_folder": str(BRONZE_EXPORT_FOLDER),
        "export_status": export_status,
    }
    return bronze_df, summary
