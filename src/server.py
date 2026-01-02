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


# ============================================
# Chat Mission Endpoints (AI-Powered Planning)
# ============================================

from .llm_core import VisionCore, Attendant
import yaml
import json

# Current plan state
CURRENT_PLAN = None

# Attendant instance (maintains conversation history)
ATTENDANT = Attendant()

class ChatRequest(BaseModel):
    message: str

class ChatMissionRequest(BaseModel):
    instruction: str

class ExecutePlanRequest(BaseModel):
    plan: list
    summary: Optional[str] = None

@app.post("/api/chat")
def chat_with_attendant(req: ChatRequest):
    """
    Attendantとの自然な会話。意図を判断し、適切に応答する。
    """
    global CURRENT_PLAN
    
    result = ATTENDANT.chat(req.message)
    
    # If a plan was generated, store it
    if result.get("plan"):
        CURRENT_PLAN = result["plan"]
    
    return result

@app.post("/api/chat/reset")
def reset_chat():
    """会話履歴をリセット"""
    global ATTENDANT, CURRENT_PLAN
    ATTENDANT = Attendant()
    CURRENT_PLAN = None
    return {"message": "Chat history cleared"}

@app.post("/api/plan")
def generate_plan(req: ChatMissionRequest):
    """
    自然言語の指示からフライトプランを生成する（実行はしない）
    """
    vision = VisionCore()
    plan_data = vision.generate_plan(req.instruction)
    
    global CURRENT_PLAN
    CURRENT_PLAN = plan_data
    
    return plan_data

@app.post("/api/execute")
def execute_plan(req: ExecutePlanRequest, background_tasks: BackgroundTasks):
    """
    生成されたプランを実行する
    """
    global CURRENT_PROCESS, CURRENT_FLIGHT_ID
    
    if CURRENT_PROCESS and CURRENT_PROCESS.poll() is None:
        raise HTTPException(status_code=400, detail="Mission already in progress")
    
    # Convert plan to YAML format for autopilot
    yaml_content = {
        "tasks": [{
            "name": req.summary or "Dynamic Mission",
            "steps": []
        }]
    }
    
    for step in req.plan:
        action = step.get("action")
        yaml_step = {"action": action}
        
        # Map parameters based on action type
        if action == "goto":
            yaml_step["url"] = step.get("url")
        elif action == "click":
            yaml_step["selector"] = step.get("selector")
            yaml_step["mode"] = step.get("mode", "hybrid")
        elif action == "click_vision":
            yaml_step["action"] = "click"
            yaml_step["mode"] = "llm"
            yaml_step["instruction"] = step.get("instruction")
        elif action == "type":
            yaml_step["selector"] = step.get("selector")
            yaml_step["text"] = step.get("text")
        elif action == "type_vision":
            yaml_step["instruction"] = step.get("instruction")
            yaml_step["text"] = step.get("text")
        elif action == "key":
            yaml_step["key"] = step.get("key")
        elif action == "read":
            yaml_step["instruction"] = step.get("instruction")
        elif action == "wait":
            yaml_step["seconds"] = step.get("seconds", 1)
        elif action == "launch_app":
            yaml_step["command"] = step.get("command")
        
        yaml_content["tasks"][0]["steps"].append(yaml_step)
    
    # Save dynamic YAML
    dynamic_yaml_path = "/workspaces/Airport/scenarios/dynamic_mission.yaml"
    with open(dynamic_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)
    
    # Initialize Flight Recorder
    CURRENT_FLIGHT_ID = history_mgr.start_flight()
    history_mgr.log_event(CURRENT_FLIGHT_ID, "PLAN", json.dumps(req.plan, ensure_ascii=False))
    
    # Run autopilot with generated YAML
    command = ["python", "run_airport.py", "web", "dynamic_mission.yaml"]
    background_tasks.add_task(run_process_wrapper, command, CURRENT_FLIGHT_ID)
    
    return {
        "message": "Mission started",
        "flight_id": CURRENT_FLIGHT_ID,
        "yaml_path": dynamic_yaml_path
    }

@app.get("/api/current_plan")
def get_current_plan():
    """現在のプランを取得"""
    return CURRENT_PLAN or {"plan": [], "summary": "No plan generated yet"}


# ============================================
# ReAct Agent Endpoints (Autonomous Mode)
# ============================================

from .react_agent import ReActAgent
from .main import ATC

# ReAct state
REACT_AGENT = None
REACT_RESULT = None
REACT_RUNNING = False
REACT_STEPS = []

class ReActRequest(BaseModel):
    goal: str
    max_steps: Optional[int] = 15

def run_react_wrapper(goal: str, flight_id: str, max_steps: int = 15):
    """ReActエージェントをバックグラウンドで実行"""
    global REACT_AGENT, REACT_RESULT, REACT_RUNNING, REACT_STEPS
    
    REACT_RUNNING = True
    REACT_STEPS = []
    
    try:
        atc = ATC()
        agent = ReActAgent(atc)
        agent.max_steps = max_steps
        REACT_AGENT = agent
        
        # コールバックで各ステップをログに記録
        def on_step(step_num, thought, screenshot):
            step_data = {
                "step": step_num,
                "observation": thought.get("observation", ""),
                "reasoning": thought.get("reasoning", ""),
                "action": thought.get("action", ""),
                "params": thought.get("params", {}),
                "screenshot": screenshot
            }
            REACT_STEPS.append(step_data)
            history_mgr.log_event(flight_id, "REACT", json.dumps(step_data, ensure_ascii=False))
        
        result = agent.run(goal, on_step=on_step)
        REACT_RESULT = result
        
        # 終了処理
        status = "COMPLETED" if result["success"] else "FAILED"
        history_mgr.log_event(flight_id, "SYSTEM", f"ReAct finished: {result['final_result']}")
        history_mgr.end_flight(flight_id, status)
        
        atc.stop_session()
        
    except Exception as e:
        REACT_RESULT = {"success": False, "error": str(e)}
        history_mgr.log_event(flight_id, "ERROR", str(e))
        history_mgr.end_flight(flight_id, "CRASHED")
    finally:
        REACT_RUNNING = False

@app.post("/api/react")
def start_react_agent(req: ReActRequest, background_tasks: BackgroundTasks):
    """
    ReActエージェントを起動（自律モード）
    画面を見ながら動的にゴールに向かって行動する
    """
    global CURRENT_FLIGHT_ID, REACT_RUNNING, REACT_STEPS, REACT_RESULT
    
    if REACT_RUNNING:
        raise HTTPException(status_code=400, detail="ReAct agent is already running")
    
    # Initialize Flight Recorder
    CURRENT_FLIGHT_ID = history_mgr.start_flight()
    REACT_STEPS = []
    REACT_RESULT = None
    
    history_mgr.log_event(CURRENT_FLIGHT_ID, "SYSTEM", f"ReAct Agent started with goal: {req.goal}")
    
    # Run in background
    background_tasks.add_task(run_react_wrapper, req.goal, CURRENT_FLIGHT_ID, req.max_steps)
    
    return {
        "message": "ReAct Agent started",
        "flight_id": CURRENT_FLIGHT_ID,
        "goal": req.goal
    }

@app.get("/api/react/status")
def get_react_status():
    """ReActエージェントの状態を取得"""
    return {
        "running": REACT_RUNNING,
        "steps": REACT_STEPS,
        "result": REACT_RESULT
    }

@app.post("/api/react/stop")
def stop_react_agent():
    """ReActエージェントを停止"""
    global REACT_RUNNING
    # Note: 現在の実装では途中停止は難しいが、フラグを立てておく
    REACT_RUNNING = False
    return {"message": "Stop signal sent"}

