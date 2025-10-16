


import pandas as pd
import os
import re
import requests
import traceback
from datetime import datetime
from simple_salesforce import Salesforce
import uuid

# ---------------------- Helper functions ----------------------

def get_excel_from_drive(file_id: str):
    """Download Excel from Google Drive and save as a unique temp file"""
    unique_filename = f"input_{uuid.uuid4().hex}.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url)
    r.raise_for_status()
    with open(unique_filename, "wb") as f:
        f.write(r.content)
    return unique_filename

def clean_company_name(name):
    if pd.isna(name) or name is None or str(name).lower() in ['nan', '', 'none']:
        return ""
    cleaned = str(name).strip()
    match = re.search(r'([A-Z0-9]+)-SD', cleaned)
    if match:
        return match.group(0)
    ticker_match = re.search(r'\(X[A-Z]*:([A-Z0-9]+)\)', cleaned)
    if ticker_match:
        return f"{ticker_match.group(1)}-SD"
    return cleaned.replace(',', ' -').replace('"', '')

def convert_excel_to_data(excel_file):
    try:
        df = pd.read_excel(excel_file, sheet_name='Nightly-Template-Template')
    except:
        df = pd.read_excel(excel_file, sheet_name=0)

    df.columns = [str(col).strip() for col in df.columns]

    # Identify columns
    stock_name_col = next((c for c in df.columns if 'stock' in c.lower() and 'name' in c.lower()), None)
    prev_close_col = next((c for c in df.columns if 'previous' in c.lower() or 'close' in c.lower()), None)
    change_col = next((c for c in df.columns if 'change' in c.lower() and c != stock_name_col), None)

    if not stock_name_col or not prev_close_col:
        return None

    records = []
    for idx, row in df.iterrows():
        try:
            stock_name = clean_company_name(row[stock_name_col])
            if not stock_name:
                continue
            prev_close = float(row[prev_close_col]) if not pd.isna(row[prev_close_col]) else None
            if prev_close is None:
                continue
            change_val = float(row[change_col]) if change_col and not pd.isna(row.get(change_col, 0)) else 0.0
            records.append({
                'Name': stock_name,
                'Previous_Close__c': prev_close,
                'Change__c': change_val
            })
        except:
            continue

    return records if records else None

def upload_to_salesforce(records):
    """Upload records to Salesforce StockData__c object"""
    try:
        # Use environment variables instead of config.properties
        username = os.environ.get("SF_USERNAME")
        password_with_token = os.environ.get("SF_PASSWORD_TOKEN")
        if not username or not password_with_token:
            return False, "Salesforce credentials missing"

        # Parse password/token
        if len(password_with_token) > 20:
            password = password_with_token[:-25]
            security_token = password_with_token[-25:]
        else:
            password = password_with_token
            security_token = ""

        sf = Salesforce(username=username, password=password, security_token=security_token)

        # Upload in batches
        batch_size = 200
        success_count = 0
        error_count = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            result = sf.bulk.StockData__c.upsert(batch, 'Name', batch_size=len(batch))
            for j, res in enumerate(result):
                if res.get('success', False):
                    success_count += 1
                else:
                    error_count += 1

        return error_count == 0, f"Uploaded: {success_count}, Failed: {error_count}"

    except Exception as e:
        return False, str(e)

def save_csv_backup(records):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f'stockdata_backup_{timestamp}.csv'
    pd.DataFrame(records).to_csv(csv_file, index=False)
    return csv_file

# ---------------------- Main function ----------------------

def main(file_id="1WuTVktuDnJh3UECy4EzeaAlH4Bm6pAY7"):
    try:
        excel_file = get_excel_from_drive(file_id)
        records = convert_excel_to_data(excel_file)
        if not records:
            return {"status": "error", "message": "No valid records found"}

        backup_file = save_csv_backup(records)
        success, msg = upload_to_salesforce(records)
        if not success:
            return {"status": "error", "message": f"Salesforce upload failed: {msg}"}

        return {"status": "success", "records_uploaded": len(records), "backup_file": backup_file}

    except Exception as e:
        return {"status": "error", "message": str(e)}
