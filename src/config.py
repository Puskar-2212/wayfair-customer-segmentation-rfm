"""
Configuration Module for RFM Customer Segmentation
Contains project constants, paths, and business parameters.
"""

from pathlib import Path
import pandas as pd

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "Datasets"
OUTPUTS_DIR = BASE_DIR / "outputs"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Datasets
ORDERS_PATH = DATASETS_DIR / "orders.csv"
ORDER_ITEMS_PATH = DATASETS_DIR / "order_items.csv"
PRODUCTS_PATH = DATASETS_DIR / "products.csv"
CUSTOMERS_PATH = DATASETS_DIR / "customers.csv"

# Output Deliverables
CUSTOMER_SEGMENTS_OUTPUT = OUTPUTS_DIR / "customer_segments.csv"
SEGMENT_SUMMARY_OUTPUT = OUTPUTS_DIR / "segment_summary.csv"

# Analysis Parameters
# Reference date specified in scenario: January 1, 2026
REFERENCE_DATE = pd.Timestamp("2026-01-01")

# Scoring Quintiles
NUM_QUINTILES = 5
SCORE_LABELS = [1, 2, 3, 4, 5]
RECENCY_LABELS = [5, 4, 3, 2, 1]  # Inverted: lower days -> higher recency score

# CRM Action Plan Dictionary
CRM_ACTION_PLAN = {
    "Champions": {
        "action": "VIP loyalty perks, early access to new lines, exclusive previews",
        "metric": "Repeat purchase rate & average order value (AOV)",
        "priority": "High Retention"
    },
    "Loyal Customers": {
        "action": "Loyalty tier rewards, personalized cross-selling, upsell recommendations",
        "metric": "Customer lifetime value (CLV) & cross-category expansion",
        "priority": "Value Maximization"
    },
    "Potential Loyalists": {
        "action": "Post-purchase engagement, category recommendations, 2nd-purchase incentive",
        "metric": "Conversion rate to 3rd qualifying purchase within 60 days",
        "priority": "Nurturing"
    },
    "New Customers": {
        "action": "Welcome onboarding drip series, brand intro, first-repeat incentive",
        "metric": "Second purchase rate within 30 days of initial order",
        "priority": "Activation"
    },
    "At Risk": {
        "action": "Personalized re-activation campaign, feedback survey, targeted discounts",
        "metric": "Reactivation rate (orders placed within 45 days)",
        "priority": "Win-Back"
    },
    "Needs Attention": {
        "action": "Engagement check-in email series, price-drop alerts on viewed categories",
        "metric": "Email open rate, click-through rate, and site re-engagement",
        "priority": "Re-engagement"
    },
    "Lost": {
        "action": "Deep discount reactivation email; if unresponsive, suppress from regular sends",
        "metric": "Reactivation rate (if < 2%, suppress to protect domain deliverability)",
        "priority": "Sunset / Cleanse"
    }
}
