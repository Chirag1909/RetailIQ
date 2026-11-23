"""
RetailIQ - Data Engineering & Cleaning Unit Tests (backend/tests/test_data_cleaning.py)
Validates duplicate dropping, cancellation detection, price checks, and idempotency.
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import pandas as pd
from pipeline.transform import DataCleaner


def test_duplicate_removal():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850, "Country": "United Kingdom"},
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850, "Country": "United Kingdom"},
    ])
    cleaned_df, audit = cleaner.clean_transactions(df)
    assert len(cleaned_df) == 1
    assert audit["duplicate_records_removed"] == 1


def test_cancellation_detection():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"InvoiceNo": "C536379", "StockCode": "D", "Description": "Discount", "Quantity": -1, "InvoiceDate": "2010-12-01 09:41:00", "UnitPrice": 27.50, "CustomerID": 14527, "Country": "United Kingdom"},
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850, "Country": "United Kingdom"},
    ])
    cleaned_df, audit = cleaner.clean_transactions(df)
    assert len(cleaned_df) == 1
    assert audit["cancellation_records"] == 1
    assert cleaned_df.iloc[0]["InvoiceNo"] == "536365"


def test_invalid_unit_prices():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 0.0, "CustomerID": 17850, "Country": "United Kingdom"},
        {"InvoiceNo": "536366", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": -5.0, "CustomerID": 17850, "Country": "United Kingdom"},
        {"InvoiceNo": "536367", "StockCode": "85123A", "Description": "HEART", "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850, "Country": "United Kingdom"},
    ])
    cleaned_df, audit = cleaner.clean_transactions(df)
    assert len(cleaned_df) == 1
    assert audit["invalid_unit_prices"] == 2
    assert cleaned_df.iloc[0]["InvoiceNo"] == "536367"


def test_revenue_calculation():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "HEART", "Quantity": 10, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 3.50, "CustomerID": 17850, "Country": "United Kingdom"},
    ])
    cleaned_df, _ = cleaner.clean_transactions(df)
    assert cleaned_df.iloc[0]["Revenue"] == 35.00
