# from flask import Flask, request, jsonify
# import traceback

# # Import your existing functions
# from final_automation import convert_excel_to_data, save_csv_backup, upload_to_salesforce

# app = Flask(__name__)

# @app.route("/process-excel", methods=["POST"])
# def process_excel():
#     try:
#         # Excel filename can come from request JSON
#         data = request.json or {}
#         excel_file = data.get("excel_file", "Nightly-Template-Template.xlsx")

#         records = convert_excel_to_data(excel_file)
#         if not records:
#             return jsonify({"status": "failed", "message": "No valid records"}), 400

#         save_csv_backup(records)

#         if not upload_to_salesforce(records):
#             return jsonify({"status": "failed", "message": "Salesforce upload failed"}), 500

#         return jsonify({
#             "status": "success",
#             "records_processed": len(records),
#             "excel_file": excel_file
#         })

#     except Exception as e:
#         return jsonify({
#             "status": "error",
#             "message": str(e),
#             "trace": traceback.format_exc()
#         }), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001)


from fastapi import FastAPI,Query
import final_automation

app = FastAPI()
API_KEY = "150697"

@app.api_route("/run-job", methods=["GET", "POST"])
def run_job(api_key: str = Query(...), file_id: str = "1PMmWg3k2If_qxKG3tUjo5oKWxgvbcjMH"):
    if api_key != API_KEY:
        return {"status": "error", "message": "Unauthorized"}
    return final_automation.main(file_id=file_id)
