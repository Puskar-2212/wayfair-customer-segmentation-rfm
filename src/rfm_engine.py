"""
RFM Calculation & Segmentation Engine
Calculates Recency, Frequency, and Monetary metrics, performs quintile scoring,
and segments customers using explicit business rules.
"""

import pandas as pd
import numpy as np
from src.config import REFERENCE_DATE, NUM_QUINTILES, SCORE_LABELS, RECENCY_LABELS


def filter_qualifying_orders(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """
    Filters for qualifying orders and computes accurate order-level net spend.

    Business Rationale:
    - 'canceled': Canceled before fulfillment, generating zero net revenue.
    - 'returned': Items were returned and refunded, reversing realized monetary value.
    - 'completed': Realized transactions reflecting verified consumer demand and value.

    Returns:
        DataFrame of qualifying completed orders with order_total.
    """
    completed = orders[orders['status'].str.lower() == 'completed'].copy()

    # Merge with line items
    merged = pd.merge(completed, order_items, on='order_id', how='left')

    # Line net revenue: (quantity * unit_price) - discount_amount
    merged['quantity'] = pd.to_numeric(merged['quantity'], errors='coerce').fillna(0)
    merged['unit_price'] = pd.to_numeric(merged['unit_price'], errors='coerce').fillna(0)
    merged['discount_amount'] = pd.to_numeric(merged['discount_amount'], errors='coerce').fillna(0)
    merged['shipping_fee'] = pd.to_numeric(merged['shipping_fee'], errors='coerce').fillna(0)

    merged['line_net_revenue'] = (merged['quantity'] * merged['unit_price']) - merged['discount_amount']

    # Aggregate to order level
    order_totals = merged.groupby(['order_id', 'customer_id', 'order_date', 'shipping_fee']).agg(
        line_net_revenue=('line_net_revenue', 'sum')
    ).reset_index()

    order_totals['order_total'] = order_totals['line_net_revenue'] + order_totals['shipping_fee']
    return order_totals


def calculate_rfm_metrics(qualifying_orders: pd.DataFrame, ref_date: pd.Timestamp = REFERENCE_DATE) -> pd.DataFrame:
    """
    Aggregates qualifying transactions by customer to calculate core RFM metrics.

    Parameters:
        qualifying_orders: Filtered order-level DataFrame
        ref_date: Snapshot cutoff date (default: January 1, 2026)

    Returns:
        DataFrame with customer_id, recency, frequency, monetary, first_order_date, last_order_date
    """
    rfm = qualifying_orders.groupby('customer_id').agg(
        last_order_date=('order_date', 'max'),
        first_order_date=('order_date', 'min'),
        frequency=('order_id', 'nunique'),
        monetary=('order_total', 'sum')
    ).reset_index()

    # Recency: days elapsed since last purchase as of reference date
    rfm['recency'] = (ref_date - rfm['last_order_date']).dt.days

    return rfm


def score_rfm_quintiles(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Scores Recency, Frequency, and Monetary measures into quintiles (1-5).
    Uses .rank(method='first') to reliably handle ties (frequent in e-commerce purchase counts).

    Returns:
        DataFrame with r_score, f_score, m_score, rfm_score
    """
    scored_rfm = rfm_df.copy()

    # Recency: Lower days = more recent = higher score (5)
    scored_rfm['r_score'] = pd.qcut(
        scored_rfm['recency'].rank(method='first', ascending=True),
        NUM_QUINTILES,
        labels=RECENCY_LABELS
    ).astype(int)

    # Frequency: Higher order count = higher score (5)
    scored_rfm['f_score'] = pd.qcut(
        scored_rfm['frequency'].rank(method='first', ascending=True),
        NUM_QUINTILES,
        labels=SCORE_LABELS
    ).astype(int)

    # Monetary: Higher spend = higher score (5)
    scored_rfm['m_score'] = pd.qcut(
        scored_rfm['monetary'].rank(method='first', ascending=True),
        NUM_QUINTILES,
        labels=SCORE_LABELS
    ).astype(int)

    # Composite RFM Score (e.g. 555 for highest tier)
    scored_rfm['rfm_score'] = (
        scored_rfm['r_score'] * 100 +
        scored_rfm['f_score'] * 10 +
        scored_rfm['m_score']
    )

    return scored_rfm


def assign_segment(row: pd.Series) -> str:
    """Classifies a customer into one of 7 distinct CRM segments."""
    r = row['r_score']
    f = row['f_score']
    m = row['m_score']

    if r >= 4 and f >= 4:
        return 'Champions'
    elif (f >= 4 and r < 4) or (f >= 3 and r >= 3 and m >= 4):
        return 'Loyal Customers'
    elif r >= 4 and f in [2, 3]:
        return 'Potential Loyalists'
    elif r >= 4 and f == 1:
        return 'New Customers'
    elif r in [2, 3] and f >= 3:
        return 'At Risk'
    elif r in [2, 3] and f in [1, 2]:
        return 'Needs Attention'
    elif r == 1:
        return 'Lost'
    else:
        return 'Needs Attention'


def segment_customers(scored_rfm: pd.DataFrame) -> pd.DataFrame:
    """Applies segment rules to the scored customer population."""
    segmented = scored_rfm.copy()
    segmented['segment'] = segmented.apply(assign_segment, axis=1)
    return segmented
