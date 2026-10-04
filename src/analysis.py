"""
Business Analysis & Hypothesis Testing Module
Computes segment-level KPIs, cohort dynamics, channel effectiveness,
and statistical contingency tests.
"""

from typing import Tuple, Dict
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from src.config import CRM_ACTION_PLAN


def compute_segment_kpis(segmented_rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Computes key performance indicators for each customer segment:
    - Customer count and share
    - Total revenue and revenue share
    - Average monetary spend per customer
    - Average order value (AOV)
    - Average recency and frequency
    - Median inter-purchase interval (days between orders)

    Returns:
        Formatted summary DataFrame
    """
    df = segmented_rfm.copy()
    total_customers = len(df)
    total_revenue = df['monetary'].sum()

    # Inter-purchase interval for customers with multiple orders
    df['days_between_orders'] = np.where(
        df['frequency'] > 1,
        (df['last_order_date'] - df['first_order_date']).dt.days / (df['frequency'] - 1),
        np.nan
    )

    summary = df.groupby('segment').agg(
        num_customers=('customer_id', 'count'),
        total_revenue=('monetary', 'sum'),
        avg_monetary=('monetary', 'mean'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        median_days_between_orders=('days_between_orders', 'median'),
        total_orders=('frequency', 'sum')
    ).reset_index()

    summary['pct_total_customers'] = (summary['num_customers'] / total_customers) * 100
    summary['pct_total_revenue'] = (summary['total_revenue'] / total_revenue) * 100
    summary['avg_order_value'] = summary['total_revenue'] / summary['total_orders']

    # Sort logically by revenue impact
    summary = summary.sort_values(by='total_revenue', ascending=False).reset_index(drop=True)

    column_order = [
        'segment', 'num_customers', 'pct_total_customers', 'total_revenue',
        'pct_total_revenue', 'avg_monetary', 'avg_order_value', 'avg_recency',
        'avg_frequency', 'median_days_between_orders'
    ]
    return summary[column_order]


def analyze_channel_attribution(
    segmented_rfm: pd.DataFrame,
    customers: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, float, bool]:
    """
    Analyzes segment distribution across customer acquisition channels
    and conducts a Chi-Square Test of Independence.

    Returns:
        Tuple: (count_crosstab, pct_crosstab, p_value, is_significant)
    """
    merged = pd.merge(
        segmented_rfm,
        customers[['customer_id', 'acquisition_channel']],
        on='customer_id',
        how='left'
    )

    count_ct = pd.crosstab(merged['segment'], merged['acquisition_channel'])
    pct_ct = pd.crosstab(merged['segment'], merged['acquisition_channel'], normalize='index') * 100

    chi2, p_val, dof, _ = chi2_contingency(count_ct)
    is_significant = p_val < 0.05

    return count_ct, pct_ct, p_val, is_significant


def analyze_signup_cohorts(
    segmented_rfm: pd.DataFrame,
    customers: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyzes customer segments by signup cohort year.

    Returns:
        Tuple: (count_crosstab, pct_crosstab)
    """
    merged = pd.merge(
        segmented_rfm,
        customers[['customer_id', 'signup_date']],
        on='customer_id',
        how='left'
    )
    merged['signup_year'] = merged['signup_date'].dt.year

    count_ct = pd.crosstab(merged['segment'], merged['signup_year'])
    pct_ct = pd.crosstab(merged['segment'], merged['signup_year'], normalize='index') * 100

    return count_ct, pct_ct


def build_crm_strategy_dataframe() -> pd.DataFrame:
    """Builds a structured tabular view of the CRM strategy, actions, and KPIs."""
    records = []
    for segment, details in CRM_ACTION_PLAN.items():
        records.append({
            "Segment": segment,
            "Strategic Priority": details["priority"],
            "Recommended CRM Action": details["action"],
            "Primary Success Metric": details["metric"]
        })
    return pd.DataFrame(records)
