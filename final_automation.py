# import pandas as pd
# import sys
# import os
# import re
# from datetime import datetime
# import traceback
# from simple_salesforce import Salesforce

# import requests


# def get_excel_from_drive(file_id: str):
#     """Download Excel from Google Drive and save as a unique temp file"""
#     unique_filename = f"input_{uuid.uuid4().hex}.xlsx"
#     url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
#     r = requests.get(url)
#     r.raise_for_status()
#     with open(unique_filename, "wb") as f:
#         f.write(r.content)
#     return unique_filename


# def clean_company_name(name):
#     """Clean company names to avoid CSV issues"""
#     if pd.isna(name) or name is None or str(name).lower() in ['nan', '', 'none']:
#         return ""
    
#     cleaned = str(name).strip()
    
#     # Extract pattern like AAOI-SD
#     match = re.search(r'([A-Z0-9]+)-SD', cleaned)
#     if match:
#         return match.group(0)
    
#     # Extract from patterns like (XNAS:AAOI)
#     ticker_match = re.search(r'\(X[A-Z]*:([A-Z0-9]+)\)', cleaned)
#     if ticker_match:
#         return f"{ticker_match.group(1)}-SD"
    
#     return cleaned.replace(',', ' -').replace('"', '')

# def convert_excel_to_data(excel_file):
#     """Convert Excel to data format for Salesforce upload"""
#     try:
#         print(f"Reading Excel file: {excel_file}")
        
#         # Read Excel sheet
#         try:
#             df = pd.read_excel(excel_file, sheet_name='Nightly-Template-Template')
#         except:
#             df = pd.read_excel(excel_file, sheet_name=0)
        
#         print(f"Read {len(df)} rows from Excel")
        
#         # Clean column names
#         df.columns = [str(col).strip() for col in df.columns]
        
#         # Find the right columns
#         stock_name_col = None
#         prev_close_col = None  
#         change_col = None
        
#         for col in df.columns:
#             col_lower = str(col).lower()
#             if 'stock' in col_lower and 'name' in col_lower:
#                 stock_name_col = col
#             elif 'previous' in col_lower or 'close' in col_lower:
#                 prev_close_col = col
#             elif 'change' in col_lower and col != stock_name_col:
#                 change_col = col
        
#         print(f"Found columns - Stock: {stock_name_col}, Close: {prev_close_col}, Change: {change_col}")
        
#         if not stock_name_col or not prev_close_col:
#             print("Could not find required columns")
#             return None
        
#         # Process data
#         records = []
        
#         for idx, row in df.iterrows():
#             try:
#                 stock_name = clean_company_name(row[stock_name_col])
                
#                 if not stock_name or stock_name.strip() == "":
#                     continue
                    
#                 try:
#                     prev_close = float(row[prev_close_col])
#                     if pd.isna(prev_close):
#                         continue
#                 except (ValueError, TypeError):
#                     continue
                
#                 # Get change value
#                 change_val = 0.0
#                 if change_col and change_col in row.index:
#                     try:
#                         change_val = float(row[change_col])
#                         if pd.isna(change_val):
#                             change_val = 0.0
#                     except (ValueError, TypeError):
#                         change_val = 0.0
                
#                 # Create record in correct format for Salesforce
#                 record = {
#                     'Name': stock_name,
#                     'Previous_Close__c': prev_close,
#                     'Change__c': change_val
#                 }
#                 records.append(record)
                
#             except Exception as e:
#                 print(f"Warning: Skipping row {idx} due to error: {e}")
#                 continue
        
#         if not records:
#             print("No valid records found")
#             return None
        
#         print(f"Processed {len(records)} valid records")
#         print(f"Sample records: {records[:3]}")
        
#         return records
        
#     except Exception as e:
#         print(f"Error processing Excel file: {e}")
#         traceback.print_exc()
#         return None

# def upload_to_salesforce(records):
#     """Upload records to Salesforce Stock_Data__c object"""
#     try:
#         # Extract credentials from config.properties
#         if not os.path.exists('config.properties'):
#             print("config.properties not found")
#             return False
        
#         with open('config.properties', 'r') as f:
#             config = f.read()
        
#         username = os.environ.get("username")
#         password_with_token = os.environ.get("password_with_token")
        
#         for line in config.split('\n'):
#             if line.startswith('sfdc.username='):
#                 username = line.split('=', 1)[1].strip()
#             elif line.startswith('sfdc.password='):
#                 password_with_token = line.split('=', 1)[1].strip()
        
#         if not username or not password_with_token:
#             print("Could not find credentials in config.properties")
#             return False
        
#         print(f"Connecting to Salesforce as: {username}")
        
#         # Parse password and security token
#         if len(password_with_token) > 20:
#             password = password_with_token[:-25] 
#             security_token = password_with_token[-25:]
#         else:
#             password = password_with_token
#             security_token = ""
        
#         # Connect to Salesforce
#         sf = Salesforce(
#             username=username,
#             password=password,
#             security_token=security_token
#         )
        
#         print("Successfully connected to Salesforce")
#         print(f"Uploading {len(records)} records to Stock_Data__c...")
        
#         success_count = 0
#         error_count = 0
        
#         # Process records in batches for better performance
#         batch_size = 200
#         for i in range(0, len(records), batch_size):
#             batch = records[i:i + batch_size]
#             print(f"Processing batch {i//batch_size + 1} ({len(batch)} records)...")
            
#             try:
#                 # Use bulk upsert with Name as external ID
#                 result = sf.bulk.Stock_Data__c.upsert(batch, 'Name', batch_size=len(batch))
                
#                 # Process results
#                 for j, res in enumerate(result):
#                     if res.get('success', False):
#                         success_count += 1
#                     else:
#                         error_count += 1
#                         record_name = batch[j].get('Name', 'unknown')
#                         errors = res.get('errors', [])
#                         error_msg = errors[0].get('message', 'Unknown error') if errors else 'Unknown error'
#                         print(f"Error upserting {record_name}: {error_msg}")
                        
#             except Exception as e:
#                 print(f"Batch {i//batch_size + 1} error: {e}")
#                 error_count += len(batch)
        
#         print(f"\nUpload Results:")
#         print(f"  Successful: {success_count}")
#         print(f"  Failed: {error_count}")
#         print(f"  Total: {len(records)}")
        
#         return error_count == 0
        
#     except Exception as e:
#         print(f"Salesforce connection/upload error: {e}")
#         traceback.print_exc()
#         return False

# def save_csv_backup(records):
#     """Save a CSV backup of the processed records"""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     csv_file = f'stockdata_backup_{timestamp}.csv'
    
#     df = pd.DataFrame(records)
#     df.to_csv(csv_file, index=False)
#     print(f"CSV backup saved: {csv_file}")

# def main():
#     print("="*60)
#     print("EXCEL TO SALESFORCE AUTOMATION - FINAL VERSION")
#     print("="*60)
    
#     file_id = "1WuTVktuDnJh3UECy4EzeaAlH4Bm6pAY7"
#     excel_file = get_excel_from_drive(file_id)
#     if len(sys.argv) > 1:
#         excel_file = sys.argv[1]
    
#     if not os.path.exists(excel_file):
#         print(f"Excel file not found: {excel_file}")
#         return False
    
#     print(f"Step 1: Processing {excel_file}...")
#     records = convert_excel_to_data(excel_file)
#     if not records:
#         return False
    
#     print(f"\nStep 2: Saving CSV backup...")
#     save_csv_backup(records)
    
#     print(f"\nStep 3: Uploading {len(records)} records to Salesforce...")
#     if not upload_to_salesforce(records):
#         print("Upload failed - check error messages above")
#         return False
    
#     print("\n" + "="*60)
#     print("AUTOMATION COMPLETED SUCCESSFULLY!")
#     print("="*60)
#     print(f"✓ Processed Excel file: {excel_file}")
#     print(f"✓ Uploaded {len(records)} records to Stock_Data__c")
#     print(f"✓ CSV backup created")
    
#     return True

# if __name__ == "__main__":
#     print(main())


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
    """Upload records to Salesforce Stock_Data__c object"""
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
            result = sf.bulk.Stock_Data__c.upsert(batch, 'Name', batch_size=len(batch))
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

def main(file_id="1PMmWg3k2If_qxKG3tUjo5oKWxgvbcjMH"):
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
