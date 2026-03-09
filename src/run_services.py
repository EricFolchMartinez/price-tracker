import subprocess
import time
import threading
import logging
from src.tracker import track_prices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

# Checks prices automaticaly every X time
def run_scheduler():
    logger.info("Scheduler started. Waiting for first cycle...")
    
    # Wait for API
    time.sleep(60) 
    
    while True:
        logger.info("Running scheduled tracking...")
        try:
            track_prices()
        except Exception as e:
            logger.error(f"Error in scheduled tracking: {e}")
        
        wait_seconds = 21600 
        logger.info(f"💤 Sleeping for {wait_seconds} seconds (6 hours)...")
        time.sleep(wait_seconds)

# FastAPI configuration
api_command = [
    "uvicorn", "src.api.main:app", 
    "--host", "0.0.0.0", "--port", "8000"
]

# Dashboard configuration
dashboard_command = [
    "streamlit", "run", "src/dashboard/app.py", 
    "--server.port=8501", "--server.address=0.0.0.0"
]

print("Starting Price Tracker Ecosystem...")

api_process = subprocess.Popen(api_command)
dashboard_process = subprocess.Popen(dashboard_command)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Keeps runing while process is alive
try:
    api_process.wait()
    dashboard_process.wait()
except KeyboardInterrupt:
    print("Stopping services...")
    api_process.terminate()
    dashboard_process.terminate()