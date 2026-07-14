"""
BI Integration Example
----------------------
Demonstrates how to use the bi_integration module to generate BI-ready datasets
and query highest sales across different products.
"""

import pandas as pd
from bi_integration import (
    generate_bi_dashboard_data,
    get_highest_sales_by_product,
    get_top_performing_customers,
    get_sales_summary_by_period,
    get_product_sales_breakdown,
    create_bi_api_response,
)


def example_highest_sales_by_product(silver_df):
    """
    Example: Get highest sales across different products/customers.
    """
    from gold import prepare_gold_data
    
    gold_df = prepare_gold_data(silver_df)
    
    # Get top 10 products/customers by sales
    top_sales = get_highest_sales_by_product(gold_df, top_n=10)
    
    print("\n" + "=" * 80)
    print("TOP 10 HIGHEST SALES")
    print("=" * 80)
    print(top_sales.to_string())
    print()
    
    return top_sales


def example_top_customers(silver_df):
    """
    Example: Get top performing customers.
    """
    from gold import prepare_gold_data
    
    gold_df = prepare_gold_data(silver_df)
    
    # Get top 5 customers by revenue
    top_customers = get_top_performing_customers(
        gold_df, metric="Total_Revenue", top_n=5
    )
    
    print("\n" + "=" * 80)
    print("TOP 5 CUSTOMERS BY REVENUE")
    print("=" * 80)
    print(top_customers.to_string())
    print()
    
    return top_customers


def example_sales_by_period(silver_df):
    """
    Example: Get sales aggregated by time period.
    """
    from gold import prepare_gold_data
    
    gold_df = prepare_gold_data(silver_df)
    
    # Get monthly sales summary
    monthly_sales = get_sales_summary_by_period(gold_df, group_by="month")
    
    print("\n" + "=" * 80)
    print("MONTHLY SALES SUMMARY")
    print("=" * 80)
    print(monthly_sales.to_string())
    print()
    
    return monthly_sales


def example_product_breakdown(silver_df):
    """
    Example: Get sales breakdown by product/source file.
    """
    from gold import build_fct_sales_transactions
    
    fct_sales = build_fct_sales_transactions(silver_df)
    
    # Get sales breakdown
    product_sales = get_product_sales_breakdown(fct_sales)
    
    print("\n" + "=" * 80)
    print("PRODUCT SALES BREAKDOWN")
    print("=" * 80)
    print(product_sales.to_string())
    print()
    
    return product_sales


def example_bi_api_response(silver_df):
    """
    Example: Create API-ready responses for BI tools.
    """
    # Example 1: Top sales API response
    top_sales_response = create_bi_api_response("top_sales", silver_df, {"top_n": 5})
    print("\n" + "=" * 80)
    print("BI API RESPONSE - TOP SALES")
    print("=" * 80)
    print(f"Status: {top_sales_response['status']}")
    print(f"Row Count: {top_sales_response['row_count']}")
    print(f"Data: {top_sales_response['data'][:3]}")  # Show first 3 records
    print()
    
    # Example 2: Product breakdown API response
    product_response = create_bi_api_response(
        "product_breakdown", silver_df, {"top_n": 10}
    )
    print("=" * 80)
    print("BI API RESPONSE - PRODUCT BREAKDOWN")
    print("=" * 80)
    print(f"Status: {product_response['status']}")
    print(f"Row Count: {product_response['row_count']}")
    if product_response["data"]:
        print(f"Sample Data: {product_response['data'][0]}")
    print()


def example_generate_full_bi_export(silver_df):
    """
    Example: Generate comprehensive BI export.
    """
    print("\n" + "=" * 80)
    print("GENERATING FULL BI EXPORT")
    print("=" * 80)
    
    summary = generate_bi_dashboard_data(silver_df)
    
    print(f"\nExport Summary:")
    print(f"  - Gold Rows: {summary['Gold_Rows']}")
    print(f"  - Fact Sales Rows: {summary['Fact_Sales_Rows']}")
    print(f"  - Customers: {summary['Customers']}")
    print(f"  - Total Revenue: ${summary['Total_Revenue']:,.2f}")
    print(f"  - Files Exported: {summary['Files_Exported']}")
    print(f"  - Export Location: {summary['Export_Location']}")
    print(f"\nExport Files:")
    for key, path in summary["Exports"].items():
        print(f"  - {key}: {path}")
    print(f"\nSummary: {summary['Summary_File']}")
    print()


if __name__ == "__main__":
    # Create sample Silver data for demonstration
    sample_silver = pd.DataFrame(
        {
            "name": ["Customer_A", "Customer_B", "Customer_A", "Customer_C"] * 3,
            "amount": [100, 150, 200, 75] * 3,
            "source_file": ["products.csv", "sales.csv", "products.csv", "sales.csv"] * 3,
            "status": ["validated"] * 12,
            "layer": ["silver"] * 12,
            "_ingestion_timestamp": ["2026-01-01T00:00:00Z"] * 12,
            "_source_system": ["uploaded"] * 12,
            "is_valid_record": [True] * 12,
            "error_reason": [""] * 12,
        }
    )
    
    print("\n" + "=" * 80)
    print("BI INTEGRATION EXAMPLES")
    print("=" * 80)
    
    # Run examples
    example_highest_sales_by_product(sample_silver)
    example_top_customers(sample_silver)
    example_sales_by_period(sample_silver)
    example_product_breakdown(sample_silver)
    example_bi_api_response(sample_silver)
    example_generate_full_bi_export(sample_silver)
    
    print("=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80)
