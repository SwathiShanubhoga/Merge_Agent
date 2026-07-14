import pandas as pd

from bronze import prepare_bronze_data
from silver import prepare_silver_data
from gold import prepare_gold_data


def test_bronze_prepares_raw_dataset():
    raw_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})

    bronze_df, summary = prepare_bronze_data([("customers.csv", raw_df)])

    assert "_ingestion_timestamp" in bronze_df.columns
    assert "_source_system" in bronze_df.columns
    assert "source_file" in bronze_df.columns
    assert bronze_df["layer"].eq("bronze").all()
    assert len(bronze_df) == 2
    assert summary["files_ingested"] == 1
    assert summary["rows_ingested"] == 2


def test_silver_standardizes_and_cleans():
    bronze_df = pd.DataFrame(
        {
            "id": [1, 2],
            "Name": [" Alice ", "bob"],
            "amount": ["10", "20"],
            "source_file": ["customers.csv", "customers.csv"],
            "layer": ["bronze", "bronze"],
            "_ingestion_timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"],
            "_source_system": ["uploaded", "uploaded"],
        }
    )

    silver_df = prepare_silver_data(bronze_df)

    assert "is_valid_record" in silver_df.columns
    assert "error_reason" in silver_df.columns
    assert "name" in silver_df.columns or "Name" in silver_df.columns
    assert silver_df["amount"].dtype.kind in "if"
    assert silver_df["status"].eq("validated").all()
    assert silver_df["layer"].eq("silver").all()
    assert len(silver_df) > 0


def test_gold_creates_business_summary():
    silver_df = pd.DataFrame(
        {
            "name": ["Alice", "Alice"],
            "amount": [10, 20],
            "source_file": ["customers.csv", "customers.csv"],
            "status": ["validated", "validated"],
            "layer": ["silver", "silver"],
            "_ingestion_timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"],
            "is_valid_record": [True, True],
            "error_reason": ["", ""],
        }
    )

    gold_df = prepare_gold_data(silver_df)

    assert "Total_Revenue" in gold_df.columns
    assert gold_df.iloc[0]["Total_Revenue"] == 30
    assert gold_df.iloc[0]["layer"] == "gold"
    assert "Transaction_Count" in gold_df.columns
    assert "Average_Transaction" in gold_df.columns
