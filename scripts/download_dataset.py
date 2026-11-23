"""
RetailIQ - Dataset Download and Initialization Script
Downloads and initializes the official UCI Online Retail Dataset:
https://archive.ics.uci.edu/dataset/352/online+retail
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
LOCAL_SOURCE_DIR = BASE_DIR / "online+retail"

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
TARGET_XLSX = DATA_RAW_DIR / "online_retail.xlsx"
TARGET_CSV = DATA_RAW_DIR / "online_retail.csv"


def download_from_uci():
    """Download the official zip file from UCI archive and extract."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    temp_zip = DATA_RAW_DIR / "online_retail_temp.zip"

    print(f"[*] Downloading official dataset from {UCI_ZIP_URL}...")
    headers = {"User-Agent": "RetailIQ-Data-Ingestion/1.0"}
    req = urllib.request.Request(UCI_ZIP_URL, headers=headers)
    
    with urllib.request.urlopen(req, timeout=60) as response, open(temp_zip, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    print("[*] Download complete. Extracting archive...")
    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith(".xlsx"):
                file_info.filename = "online_retail.xlsx"
                zip_ref.extract(file_info, DATA_RAW_DIR)
                break

    if temp_zip.exists():
        temp_zip.unlink()
    print(f"[+] Dataset successfully extracted to {TARGET_XLSX}")


def setup_dataset():
    """Ensure raw dataset is in place and converted to high-performance CSV."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Check if raw CSV already exists
    if TARGET_CSV.exists() and TARGET_CSV.stat().st_size > 1000000:
        print(f"[+] Target CSV already initialized: {TARGET_CSV} ({TARGET_CSV.stat().st_size:,} bytes)")
        return TARGET_CSV

    # Check if local xlsx exists in online+retail folder
    existing_xlsx = None
    if TARGET_XLSX.exists() and TARGET_XLSX.stat().st_size > 1000000:
        existing_xlsx = TARGET_XLSX
    elif (LOCAL_SOURCE_DIR / "Online Retail.xlsx").exists():
        existing_xlsx = LOCAL_SOURCE_DIR / "Online Retail.xlsx"

    if existing_xlsx:
        print(f"[*] Found local official dataset at: {existing_xlsx}")
        if not TARGET_XLSX.exists():
            print(f"[*] Copying to {TARGET_XLSX}...")
            shutil.copy2(existing_xlsx, TARGET_XLSX)
    else:
        print("[!] No local Excel file found. Initiating remote download...")
        try:
            download_from_uci()
        except Exception as e:
            print(f"[!] Remote download failed: {e}")
            sys.exit(1)

    # Convert XLSX to CSV for fast downstream ETL
    print("[*] Converting Excel dataset to high-performance CSV...")
    df = pd.read_excel(TARGET_XLSX)
    print(f"[*] Loaded {len(df):,} records with columns: {list(df.columns)}")
    df.to_csv(TARGET_CSV, index=False)
    print(f"[+] Successfully generated: {TARGET_CSV} ({TARGET_CSV.stat().st_size:,} bytes)")
    return TARGET_CSV


if __name__ == "__main__":
    setup_dataset()
