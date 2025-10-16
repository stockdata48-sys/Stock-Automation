


from fastapi import FastAPI,Query
import final_automation

app = FastAPI()
API_KEY = "150697"

@app.api_route("/run-job", methods=["GET", "POST"])
def run_job(api_key: str = Query(...), file_id: str = "1PMmWg3k2If_qxKG3tUjo5oKWxgvbcjMH"):
    if api_key != API_KEY:
        return {"status": "error", "message": "Unauthorized"}
    return final_automation.main(file_id=file_id)
