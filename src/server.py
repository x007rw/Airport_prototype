from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import glob
from typing import List, Optional

app = FastAPI(title="Airport Cockpit API")

# CORS Setup (Allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task State
CURRENT_PROCESS = None
LOG_FILE = "/workspaces/Airport/results/server_execution.log"

class RunRequest(BaseModel):
    mode: str # "web", "desktop", "weather_demo"
    scenario: Optional[str] = None

def run_process(command: List[str]):
    global CURRENT_PROCESS
    # Ensure results dir exists
    os.makedirs("/workspaces/Airport/results", exist_ok=True)
    
    with open(LOG_FILE, "w") as f:
        # Use line buffering
        CURRENT_PROCESS = subprocess.Popen(
            command,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd="/workspaces/Airport",
            env={**os.environ, "PYTHONPATH": f"{os.environ.get('PYTHONPATH', '')}:."}
        )

@app.get("/api/status")
def get_status():
    global CURRENT_PROCESS
    is_running = CURRENT_PROCESS is not None and CURRENT_PROCESS.poll() is None
    return {"status": "running" if is_running else "idle"}

@app.post("/api/run")
def run_mission(req: RunRequest, background_tasks: BackgroundTasks):
    global CURRENT_PROCESS
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

    background_tasks.add_task(run_process, command)
    return {"message": f"Mission {req.mode} started"}

@app.get("/api/logs")
def get_logs():
    if not os.path.exists(LOG_FILE):
        return {"logs": "No logs yet."}
    with open(LOG_FILE, "r") as f:
        content = f.read()
    return {"logs": content}

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
