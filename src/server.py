from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import glob
from typing import List, Optional
import time
import threading
from .history_manager import HistoryManager

# Initialize API and History Manager
app = FastAPI(title="Airport Cockpit API")
history_mgr = HistoryManager()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task State
CURRENT_PROCESS = None
CURRENT_FLIGHT_ID = None
LOG_FILE = "/workspaces/Airport/results/server_execution.log"

class RunRequest(BaseModel):
    mode: str # "web", "desktop", "weather_demo"
    scenario: Optional[str] = None

def run_process_wrapper(command: List[str], flight_id: str):
    global CURRENT_PROCESS
    
    # Log start
    history_mgr.log_event(flight_id, "SYSTEM", f"Command initiated: {' '.join(command)}")
    
    # Ensure results dir exists
    os.makedirs("/workspaces/Airport/results", exist_ok=True)
    
    with open(LOG_FILE, "w") as f:
        try:
            CURRENT_PROCESS = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd="/workspaces/Airport",
                env={**os.environ, "PYTHONPATH": f"{os.environ.get('PYTHONPATH', '')}:."},
                text=True,
                bufsize=1
            )
            
            # Real-time logging
            for line in iter(CURRENT_PROCESS.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    f.write(clean_line + "\n")
                    f.flush()
                    # Also log to Black Box
                    history_mgr.log_event(flight_id, "ACTION", clean_line)
            
            CURRENT_PROCESS.stdout.close()
            return_code = CURRENT_PROCESS.wait()
            
            status = "COMPLETED" if return_code == 0 else "FAILED"
            msg = f"Mission finished with code {return_code}"
            
            history_mgr.log_event(flight_id, "SYSTEM", msg)
            history_mgr.end_flight(flight_id, status)
            
            # Final log write
            f.write(f"\n[SYSTEM] {msg}\n")
            
        except Exception as e:
            err_msg = f"Execution Error: {str(e)}"
            f.write(f"\n[ERROR] {err_msg}\n")
            history_mgr.log_event(flight_id, "ERROR", err_msg)
            history_mgr.end_flight(flight_id, "CRASHED")

@app.get("/api/status")
def get_status():
    global CURRENT_PROCESS
    is_running = CURRENT_PROCESS is not None and CURRENT_PROCESS.poll() is None
    return {"status": "running" if is_running else "idle"}

@app.post("/api/run")
def run_mission(req: RunRequest, background_tasks: BackgroundTasks):
    global CURRENT_PROCESS, CURRENT_FLIGHT_ID
    
    if CURRENT_PROCESS and CURRENT_PROCESS.poll() is None:
        raise HTTPException(status_code=400, detail="Mission already in progress")

    command = []
    if req.mode == "web":
        if not req.scenario:
             raise HTTPException(status_code=400, detail="Scenario required for web mode")
        command = ["python", "run_airport.py", "web", req.scenario]
    elif req.mode == "desktop":
        command = ["python", "run_airport.py", "desktop"]
    elif req.mode == "weather_demo":
        command = ["python", "scripts/task_weather.py"]
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    # Initialize Flight Recorder
    CURRENT_FLIGHT_ID = history_mgr.start_flight()
    
    # Run in background
    background_tasks.add_task(run_process_wrapper, command, CURRENT_FLIGHT_ID)
    
    return {"message": f"Mission {req.mode} started", "flight_id": CURRENT_FLIGHT_ID}

@app.get("/api/logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return {"logs": "No logs yet."}
    with open(LOG_FILE, "r") as f:
        content = f.read()
    return {"logs": content}

@app.get("/api/flights")
def get_flights():
    """過去のフライト一覧を取得"""
    return {"flights": history_mgr.get_all_flights()}

@app.get("/api/flights/{flight_id}")
def get_flight_details(flight_id: str):
    """特定のフライトの詳細ログを取得"""
    return {
        "metadata": history_mgr._load_json(flight_id, "metadata.json"),
        "logs": history_mgr.get_flight_data(flight_id)
    }

@app.get("/api/videos")
def get_videos():
    video_dir = "/workspaces/Airport/results/videos"
    if not os.path.exists(video_dir):
        return []
    files = glob.glob(os.path.join(video_dir, "*.webm"))
    files.sort(key=os.path.getmtime, reverse=True)
    return [os.path.basename(f) for f in files]

@app.get("/api/videos/{filename}")
def stream_video(filename: str):
    video_path = os.path.join("/workspaces/Airport/results/videos", filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video_path, media_type="video/webm")
