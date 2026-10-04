"""
Data Loading and Ingestion Module
Handles loading raw datasets, validation, missing value imputation, and cleaning.
"""

from typing import Dict, Tuple
import pandas as pd
from src.config import ORDERS_PATH, ORDER_ITEMS_PATH, PRODUCTS_PATH, CUSTOMERS_PATH


def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads all four raw datasets from the Datasets directory.

    Returns:
        Tuple containing (orders, order_items, products, customers)
    """
    orders = pd.read_csv(ORDERS_PATH)
    order_items = pd.read_csv(ORDER_ITEMS_PATH)
    products = pd.read_csv(PRODUCTS_PATH)
    customers = pd.read_csv(CUSTOMERS_PATH)
    return orders, order_items, products, customers


def clean_datasets(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Cleans datasets by removing duplicates, imputing missing values with catalog data,
    normalizing categorical variables, and parsing timestamps.

    Returns:
        Cleaned copies of (orders, order_items, products, customers)
    """
    orders_clean = orders.copy()
    items_clean = order_items.copy()
    products_clean = products.copy()
    customers_clean = customers.copy()

    # 1. Parse timestamps
    orders_clean['order_date'] = pd.to_datetime(orders_clean['order_date'], errors='coerce')
    customers_clean['signup_date'] = pd.to_datetime(customers_clean['signup_date'], errors='coerce')

    # 2. Strip whitespace from string columns (preserving NaN values)
    for df in [orders_clean, items_clean, products_clean, customers_clean]:
        str_cols = df.select_dtypes(include=['object']).columns
        for col in str_cols:
            df[col] = df[col].str.strip()

    # 3. Deduplicate orders on order_id
    initial_orders = len(orders_clean)
    orders_clean = orders_clean.drop_duplicates(subset=['order_id'], keep='first')
    removed_duplicates = initial_orders - len(orders_clean)

    # 4. Standardize product categories (Title Casing)
    if 'category' in products_clean.columns:
        products_clean['category'] = products_clean['category'].str.title()

    # 5. Impute missing unit_price in order_items from product catalog list_price
    missing_price_count = items_clean['unit_price'].isnull().sum()
    if missing_price_count > 0:
        items_clean = items_clean.merge(
            products_clean[['product_id', 'list_price']],
            on='product_id',
            how='left'
        )
        items_clean['unit_price'] = items_clean['unit_price'].fillna(items_clean['list_price'])
        
        # Fallback to catalog median if any remain unmapped
        if items_clean['unit_price'].isnull().sum() > 0:
            items_clean['unit_price'] = items_clean['unit_price'].fillna(items_clean['unit_price'].median())
            
        items_clean = items_clean.drop(columns=['list_price'], errors='ignore')

    # 6. Ensure discount amount defaults to 0 if NaN
    items_clean['discount_amount'] = items_clean['discount_amount'].fillna(0.0)
    orders_clean['shipping_fee'] = orders_clean['shipping_fee'].fillna(0.0)

    return orders_clean, items_clean, products_clean, customers_clean


def get_cleaning_summary(
    raw_orders: pd.DataFrame,
    clean_orders: pd.DataFrame,
    raw_items: pd.DataFrame,
    clean_items: pd.DataFrame,
    clean_products: pd.DataFrame,
    clean_customers: pd.DataFrame
) -> Dict[str, any]:
    """Generates an audit dictionary summarizing data hygiene and cleaning metrics."""
    return {
        "raw_orders_count": len(raw_orders),
        "clean_orders_count": len(clean_orders),
        "duplicate_orders_removed": len(raw_orders) - len(clean_orders),
        "raw_items_count": len(raw_items),
        "clean_items_count": len(clean_items),
        "missing_prices_imputed": int(raw_items['unit_price'].isnull().sum()),
        "products_count": len(clean_products),
        "unique_categories": clean_products['category'].nunique(),
        "total_registered_customers": len(clean_customers),
        "date_range_start": clean_orders['order_date'].min(),
        "date_range_end": clean_orders['order_date'].max()
    }
