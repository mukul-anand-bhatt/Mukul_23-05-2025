from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
from report import generate_report, generate_single_store_report
from db import init_db, load_data, ingest_new_data
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Store Monitoring System", description="API for monitoring restaurant uptime/downtime")
scheduler = BackgroundScheduler()

# Global dictionary to store report status
report_status = {}

@app.on_event("startup")
async def startup_event():
    """Initialize database and load data on startup"""
    print("Initializing database...")
    init_db()
    print("Loading data...")
    load_data()
    print("Application startup complete!")
    # Start periodic ingestion every 10 minutes to simulate hourly polling
    try:
        scheduler.add_job(ingest_new_data, 'interval', minutes=10, id='ingest_job', replace_existing=True)
        scheduler.start()
        print("BackgroundScheduler started: ingest_new_data every 10 minutes")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

@app.get("/")
async def root():
    return {"message": "Store Monitoring System API", "status": "running"}

@app.on_event("shutdown")
async def shutdown_event():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass

@app.post("/trigger_report")
async def trigger_report():
    """
    Trigger report generation from the data stored in DB
    Returns a random report_id for polling
    """
    try:
        # Generate a unique report ID
        report_id = str(uuid.uuid4())
        
        # Initialize status as "Running"
        report_status[report_id] = "Running"
        
        # Start report generation in a background thread
        def generate_report_async():
            try:
                generate_report(report_id)
                # Check if CSV file was created successfully
                csv_path = f"output/{report_id}.csv"
                if os.path.exists(csv_path):
                    report_status[report_id] = "Complete"
                else:
                    report_status[report_id] = "Failed: CSV file not created"
            except Exception as e:
                report_status[report_id] = f"Failed: {str(e)}"
        
        thread = threading.Thread(target=generate_report_async)
        thread.daemon = True
        thread.start()
        
        return {"report_id": report_id, "status": "Report generation started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger report: {str(e)}")

@app.get("/get_report/{report_id}")
async def get_report(report_id: str):
    """
    Get the status of a report or download the CSV file
    """
    try:
        # Check if report exists
        if report_id not in report_status:
            raise HTTPException(status_code=404, detail="Report not found")
        
        status = report_status[report_id]
        
        # If report is still running
        if status == "Running":
            return {"status": "Running"}
        
        # If report failed
        if status.startswith("Failed"):
            return {"status": status}
        
        # If report is complete, return the CSV file
        if status == "Complete":
            csv_path = f"output/{report_id}.csv"
            if os.path.exists(csv_path):
                return FileResponse(
                    path=csv_path,
                    filename=f"store_report_{report_id}.csv",
                    media_type="text/csv"
                )
            else:
                report_status[report_id] = "Failed: CSV file not found"
                return {"status": "Failed: CSV file not found"}
        
        return {"status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

@app.get("/reports")
async def list_reports():
    """List all reports and their statuses"""
    return {"reports": report_status}

@app.post("/trigger_single_store_report/{store_id}")
async def trigger_single_store_report(store_id: str):
    """
    Trigger report generation for a single store
    """
    try:
        # Generate a unique report ID
        report_id = f"single_store_{store_id}_{str(uuid.uuid4())[:8]}"
        
        # Initialize status as "Running"
        report_status[report_id] = "Running"
        
        # Start report generation in a background thread
        def generate_single_report_async():
            try:
                generate_single_store_report(report_id, store_id)
                # Check if CSV file was created successfully
                csv_path = f"output/{report_id}.csv"
                if os.path.exists(csv_path):
                    report_status[report_id] = "Complete"
                else:
                    report_status[report_id] = "Failed: CSV file not created"
            except Exception as e:
                report_status[report_id] = f"Failed: {str(e)}"
        
        thread = threading.Thread(target=generate_single_report_async)
        thread.daemon = True
        thread.start()
        
        return {"report_id": report_id, "store_id": store_id, "status": "Single store report generation started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger single store report: {str(e)}")

@app.post("/ingest")
async def ingest_endpoint():
    """Manually trigger ingestion of new data."""
    try:
        ingest_new_data()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/store_summary/{store_id}")
async def get_store_summary(store_id: str):
    """
    Get a quick summary of store data availability
    """
    try:
        from report import get_store_summary
        summary = get_store_summary(store_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting store summary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
