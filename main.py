"""
Main Pipeline Runner
Orchestrates the end-to-end RFM Customer Segmentation workflow for Wayfair.
"""

import sys
import time
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    REFERENCE_DATE,
    CUSTOMER_SEGMENTS_OUTPUT,
    SEGMENT_SUMMARY_OUTPUT,
    OUTPUTS_DIR
)
from src.data_loader import load_raw_data, clean_datasets, get_cleaning_summary
from src.rfm_engine import (
    filter_qualifying_orders,
    calculate_rfm_metrics,
    score_rfm_quintiles,
    segment_customers
)
from src.analysis import (
    compute_segment_kpis,
    analyze_channel_attribution,
    analyze_signup_cohorts,
    build_crm_strategy_dataframe
)
from src.visualization import generate_all_visualizations


def print_banner(text: str):
    """Prints a styled CLI banner."""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}\n")


def run_pipeline():
    """Executes the complete customer segmentation pipeline."""
    start_time = time.time()
    print_banner("WAYFAIR CUSTOMER SEGMENTATION PIPELINE (RFM)")

    # 1. Ingestion & Cleaning
    print("[1/6] Ingesting and Cleaning Datasets...")
    orders_raw, items_raw, products_raw, customers_raw = load_raw_data()
    orders, items, products, customers = clean_datasets(
        orders_raw, items_raw, products_raw, customers_raw
    )
    cleaning_metrics = get_cleaning_summary(
        orders_raw, orders, items_raw, items, products, customers
    )
    print(f"  - Orders: {cleaning_metrics['clean_orders_count']:,} (Removed {cleaning_metrics['duplicate_orders_removed']} duplicates)")
    print(f"  - Items:  {cleaning_metrics['clean_items_count']:,} (Imputed {cleaning_metrics['missing_prices_imputed']} missing unit prices)")
    print(f"  - Products: {cleaning_metrics['products_count']} in {cleaning_metrics['unique_categories']} categories")
    print(f"  - Customer Accounts: {cleaning_metrics['total_registered_customers']:,}")

    # 2. Qualifying Orders
    print("\n[2/6] Filtering Qualifying Orders...")
    qualifying_orders = filter_qualifying_orders(orders, items)
    print(f"  - Total completed qualifying orders: {len(qualifying_orders):,}")
    print(f"  - Total realized net sales: ${qualifying_orders['order_total'].sum():,.2f}")

    # 3. RFM Calculation & Quintile Scoring
    print(f"\n[3/6] Computing RFM Metrics (Cutoff: {REFERENCE_DATE.strftime('%Y-%m-%d')})...")
    rfm_metrics = calculate_rfm_metrics(qualifying_orders, ref_date=REFERENCE_DATE)
    print(f"  - Qualifying active customers: {len(rfm_metrics):,}")

    scored_rfm = score_rfm_quintiles(rfm_metrics)
    segmented_rfm = segment_customers(scored_rfm)

    # 4. KPI Aggregation & Statistical Tests
    print("\n[4/6] Aggregating Segment KPIs & Attribution Dynamics...")
    summary_df = compute_segment_kpis(segmented_rfm)
    print("\nSegment Summary:")
    print(summary_df.to_string(index=False))

    _, _, channel_p_value, is_significant = analyze_channel_attribution(segmented_rfm, customers)
    print(f"\nChannel Attribution Significance (Chi-square): p-value = {channel_p_value:.4e} (Significant: {is_significant})")

    crm_strategy_df = build_crm_strategy_dataframe()
    print("\nRecommended CRM Action Matrix:")
    print(crm_strategy_df.to_string(index=False))

    # 5. Visualizations
    print(f"\n[5/6] Generating Publication Visualizations into {OUTPUTS_DIR}...")
    generate_all_visualizations(segmented_rfm, summary_df, customers, output_dir=OUTPUTS_DIR)
    print("  - Generated 6 high-resolution charts.")

    # 6. Deliverable Exports
    print("\n[6/6] Exporting Final Deliverable Files...")
    export_columns = [
        'customer_id', 'recency', 'frequency', 'monetary',
        'r_score', 'f_score', 'm_score', 'rfm_score', 'segment'
    ]
    segmented_rfm[export_columns].to_csv(CUSTOMER_SEGMENTS_OUTPUT, index=False)
    summary_df.to_csv(SEGMENT_SUMMARY_OUTPUT, index=False)
    print(f"  - Saved: {CUSTOMER_SEGMENTS_OUTPUT}")
    print(f"  - Saved: {SEGMENT_SUMMARY_OUTPUT}")

    elapsed = time.time() - start_time
    print_banner(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f}s")


if __name__ == "__main__":
    run_pipeline()
