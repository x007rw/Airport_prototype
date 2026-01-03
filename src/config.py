import os
from pathlib import Path

# Base paths
WORKSPACE_ROOT = Path("/workspaces/Airport")
RESULTS_DIR = WORKSPACE_ROOT / "results"
FLIGHTS_DIR = RESULTS_DIR / "flights"
VIDEOS_DIR = RESULTS_DIR / "videos"
REACT_SCREENSHOTS_DIR = RESULTS_DIR / "react_screenshots"
LOGS_DIR = RESULTS_DIR / "logs"
SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"
DESKTOP_LOGS_DIR = RESULTS_DIR / "desktop_logs"
DESKTOP_SCREENSHOTS_DIR = RESULTS_DIR / "desktop_screenshots"

# UI / recording defaults
VIEWPORT_SIZE = {"width": 1280, "height": 720}
DISPLAY = os.getenv("DISPLAY", ":99")

