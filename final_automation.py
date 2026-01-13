
# import pandas as pd
# import os
# import re
# import requests
# import traceback
# from datetime import datetime
# from simple_salesforce import Salesforce
# import uuid
# import sys

# # ---------------------- Helper functions ----------------------

# def get_excel_from_drive(file_id: str):
#     """Download Excel from Google Drive and save as a unique temp file"""
#     print(f"Downloading from Drive: {file_id}", flush=True)
#     unique_filename = f"input_{uuid.uuid4().hex}.xlsx"
#     url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
#     r = requests.get(url)
#     r.raise_for_status()
#     with open(unique_filename, "wb") as f:
#         f.write(r.content)
#     print(f"Downloaded to: {unique_filename}", flush=True)
#     return unique_filename

# def clean_company_name(name):
#     if pd.isna(name) or name is None or str(name).lower() in ['nan', '', 'none']:
#         return ""
#     cleaned = str(name).strip()
#     match = re.search(r'([A-Z0-9]+)-SD', cleaned)
#     if match:
#         return match.group(0)
#     ticker_match = re.search(r'\(X[A-Z]*:([A-Z0-9]+)\)', cleaned)
#     if ticker_match:
#         return f"{ticker_match.group(1)}-SD"
#     return cleaned.replace(',', ' -').replace('"', '')

# def convert_excel_to_data(excel_file):
#     print(f"Reading Excel file: {excel_file}", flush=True)
#     try:
#         df = pd.read_excel(excel_file, sheet_name='Nightly-Template-Template')
#     except:
#         df = pd.read_excel(excel_file, sheet_name=0)

#     df.columns = [str(col).strip() for col in df.columns]
#     print(f"Columns found: {df.columns.tolist()}", flush=True)

#     # Identify columns
#     stock_name_col = next((c for c in df.columns if 'stock' in c.lower() and 'name' in c.lower()), None)
#     prev_close_col = next((c for c in df.columns if 'previous' in c.lower() or 'close' in c.lower()), None)
#     change_col = next((c for c in df.columns if 'change' in c.lower() and c != stock_name_col), None)

#     print(f"Stock column: {stock_name_col}", flush=True)
#     print(f"Previous close column: {prev_close_col}", flush=True)
#     print(f"Change column: {change_col}", flush=True)

#     if not stock_name_col or not prev_close_col:
#         print("ERROR: Required columns not found!", flush=True)
#         return None

#     records = []
#     for idx, row in df.iterrows():
#         try:
#             stock_name = clean_company_name(row[stock_name_col])
#             if not stock_name:
#                 continue
#             prev_close = float(row[prev_close_col]) if not pd.isna(row[prev_close_col]) else None
#             if prev_close is None:
#                 continue
#             change_val = float(row[change_col]) if change_col and not pd.isna(row.get(change_col, 0)) else 0.0
#             records.append({
#                 'Name': stock_name,
#                 'PreviousClose__c': prev_close,
#                 'Change__c': change_val
#             })
#         except Exception as e:
#             print(f"Error processing row {idx}: {e}", flush=True)
#             continue

#     print(f"Total records parsed: {len(records)}", flush=True)
#     if records:
#         print(f"Sample record: {records[0]}", flush=True)
#     return records if records else None

# def upload_to_salesforce(records):
#     """Upload records to Salesforce StockData__c object"""
#     try:
#         print("Connecting to Salesforce...", flush=True)
#         username = os.environ.get("SF_USERNAME")
#         password_with_token = os.environ.get("SF_PASSWORD_TOKEN")
        
#         print(f"Username set: {bool(username)}", flush=True)
#         print(f"Password set: {bool(password_with_token)}", flush=True)
        
#         if not username or not password_with_token:
#             return False, "Salesforce credentials missing"

#         # Parse password/token
#         if len(password_with_token) > 20:
#             password = password_with_token[:-25]
#             security_token = password_with_token[-25:]
#         else:
#             password = password_with_token
#             security_token = ""

#         print("Attempting login...", flush=True)
#         sf = Salesforce(username=username, password=password, security_token=security_token)
#         print("Login successful!", flush=True)

#         # Upload in batches
#         batch_size = 200
#         success_count = 0
#         error_count = 0
#         print(f"Uploading {len(records)} records...", flush=True)
        
#         for i in range(0, len(records), batch_size):
#             batch = records[i:i + batch_size]
#             print(f"Uploading batch {i//batch_size + 1}...", flush=True)
#             result = sf.bulk.StockData__c.upsert(batch, 'Name', batch_size=len(batch))
#             for j, res in enumerate(result):
#                 if res.get('success', False):
#                     success_count += 1
#                 else:
#                     error_count += 1
#                     print(f"Failed record: {res}", flush=True)

#         msg = f"Uploaded: {success_count}, Failed: {error_count}"
#         print(msg, flush=True)
#         return error_count == 0, msg

#     except Exception as e:
#         error_msg = f"Salesforce error: {str(e)}"
#         print(error_msg, flush=True)
#         print(traceback.format_exc(), flush=True)
#         return False, error_msg

# def save_csv_backup(records):
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     csv_file = f'stockdata_backup_{timestamp}.csv'
#     pd.DataFrame(records).to_csv(csv_file, index=False)
#     print(f"Backup saved: {csv_file}", flush=True)
#     return csv_file

# # ---------------------- Main function ----------------------

# def main(file_id="1DPWARP9_7p0NoTNptsl7sxPvGekQYET6Jcw4BXYBu4I"):
#     print("=" * 50, flush=True)
#     print("STARTING STOCK AUTOMATION JOB", flush=True)
#     print("=" * 50, flush=True)
    
#     try:
#         excel_file = get_excel_from_drive(file_id)
#         records = convert_excel_to_data(excel_file)
        
#         if not records:
#             print("ERROR: No valid records found", flush=True)
#             return {"status": "error", "message": "No valid records found"}

#         backup_file = save_csv_backup(records)
#         success, msg = upload_to_salesforce(records)
        
#         if not success:
#             print(f"UPLOAD FAILED: {msg}", flush=True)
#             return {"status": "error", "message": f"Salesforce upload failed: {msg}"}

#         print("JOB COMPLETED SUCCESSFULLY", flush=True)
#         return {"status": "success", "records_uploaded": len(records), "backup_file": backup_file}

#     except Exception as e:
#         error_msg = f"Fatal error: {str(e)}"
#         print(error_msg, flush=True)
#         print(traceback.format_exc(), flush=True)
#         return {"status": "error", "message": error_msg}
# #         return {"status": "success", "records_uploaded": len(records), "backup_file": backup_file}

# #     except Exception as e:
# #         return {"status": "error", "message": str(e)}





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
    unique_filename = f"input_{uuid.uuid4().hex}.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url)
    r.raise_for_status()
    with open(unique_filename, "wb") as f:
        f.write(r.content)
    return unique_filename


def clean_company_name(name):
    if pd.isna(name) or str(name).strip() == "":
        return ""

    cleaned = str(name).strip()

    match = re.search(r'([A-Z0-9]+)-SD', cleaned)
    if match:
        return match.group(0)

    ticker_match = re.search(r'\(X[A-Z]*:([A-Z0-9]+)\)', cleaned)
    if ticker_match:
        return f"{ticker_match.group(1)}-SD"

    return cleaned.replace(',', '').replace('"', '')


def to_float(val):
    if pd.isna(val):
        return None
    try:
        return float(str(val).replace('$', '').replace(',', '').strip())
    except:
        return None


def convert_excel_to_data(excel_file):
    try:
        df = pd.read_excel(excel_file, sheet_name='Nightly-Template-Template')
    except:
        df = pd.read_excel(excel_file, sheet_name=0)

    df.columns = [str(col).strip() for col in df.columns]

    stock_col = next((c for c in df.columns if 'stock' in c.lower()), None)
    prev_close_col = next((c for c in df.columns if 'previous' in c.lower()), None)
    change_col = next((c for c in df.columns if 'change' in c.lower()), None)

    if not stock_col or not prev_close_col:
        return None

    # Prevent duplicate upserts
    df = df.drop_duplicates(subset=[stock_col])

    records = []
    for _, row in df.iterrows():
        stock_name = clean_company_name(row[stock_col])
        if not stock_name:
            continue

        prev_close = to_float(row[prev_close_col])
        if prev_close is None:
            continue

        change_val = to_float(row[change_col]) if change_col else 0.0
        change_val = change_val if change_val is not None else 0.0

        records.append({
            "Name": stock_name,
            "PreviousClose__c": prev_close,
            "Change__c": change_val
        })

    return records if records else None


def save_csv_backup(records):
    filename = f"stockdata_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(records).to_csv(filename, index=False)
    return filename


def upload_to_salesforce(records):
    try:
        username = os.environ.get("SF_USERNAME")
        password_token = os.environ.get("SF_PASSWORD_TOKEN")

        if not username or not password_token:
            return {
                "status": "error",
                "message": "Missing Salesforce credentials"
            }

        password = password_token[:-25]
        token = password_token[-25:]

        sf = Salesforce(username=username, password=password, security_token=token)

        batch_size = 500
        success_count = 0
        error_count = 0
        failed_rows = []

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            results = sf.bulk.StockData__c.upsert(batch, 'Name')

            for j, res in enumerate(results):
                if res.get("success"):
                    success_count += 1
                else:
                    error_count += 1

                    # ✅ FIX: Properly parse Salesforce error objects
                    error_messages = []
                    for e in res.get("errors", []):
                        if isinstance(e, dict):
                            error_messages.append(
                                f"{e.get('statusCode')}: {e.get('message')} (fields: {e.get('fields')})"
                            )
                        else:
                            error_messages.append(str(e))

                    failed_rows.append({
                        "row_index": i + j,
                        "name": batch[j].get("Name"),
                        "errors": "; ".join(error_messages)
                    })

        failed_csv = None
        if failed_rows:
            failed_csv = f"failed_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            pd.DataFrame(failed_rows).to_csv(failed_csv, index=False)

        if error_count > 0:
            return {
                "status": "partial_success",
                "uploaded": success_count,
                "failed": error_count,
                "failed_records_file": failed_csv
            }

        return {
            "status": "success",
            "uploaded": success_count
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }


# ---------------------- Main function ----------------------

def main(file_id="1DPWARP9_7p0NoTNptsl7sxPvGekQYET6Jcw4BXYBu4I"):
    try:
        excel_file = get_excel_from_drive(file_id)
        records = convert_excel_to_data(excel_file)

        if not records:
            return {"status": "error", "message": "No valid records found"}

        backup_file = save_csv_backup(records)
        result = upload_to_salesforce(records)
        result["backup_file"] = backup_file
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
