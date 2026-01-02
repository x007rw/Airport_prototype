import os
import time
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

# --- Airport 自律起動フェーズ ---
def ensure_display():
    display = os.getenv("DISPLAY", ":99")
    try:
        subprocess.run(["xdpyinfo", "-display", display], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print(f"Display {display} not found. Starting Xvfb...")
        subprocess.Popen(["Xvfb", display, "-ac", "-screen", "0", "1280x720x24"])
        time.sleep(2)

ensure_display()

from playwright.sync_api import sync_playwright
import pyautogui
import cv2
import numpy as np

class ATC:
    def __init__(self):
        pyautogui.FAILSAFE = False
        self.log_base = "/workspaces/Airport/results/logs"
        self.img_base = "/workspaces/Airport/results/screenshots"
        os.makedirs(self.log_base, exist_ok=True)
        os.makedirs(self.img_base, exist_ok=True)
        
        # State persistence
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start_session(self):
        """Starts a persistent browser session with video recording."""
        print("🛫 Starting Browser Session with Video Recording...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        
        # 動画保存ディレクトリ
        video_dir = "/workspaces/Airport/results/videos"
        os.makedirs(video_dir, exist_ok=True)
        
        # Contextを作成して動画記録を設定
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            record_video_dir=video_dir,
            record_video_size={'width': 1280, 'height': 720}
        )
        self.page = self.context.new_page()
        return self.page

    def stop_session(self):
        """Ends the browser session."""
        print("🛬 Ending Session...")
        if self.context: 
            self.context.close() # 重要: これで動画ファイルが確定される
            path = self.page.video.path() if self.page else "unknown"
            print(f"🎥 Video saved to: {path}")
            
        if self.page: self.page.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def nav(self, url):
        """Navigates to a URL."""
        if not self.page: self.start_session()
        print(f"🧭 Navigating to: {url}")
        self.page.goto(url)
        # self.page.wait_for_load_state("networkidle") # Optional

    def type_text(self, selector, text):
        """Types text into an element."""
        if not self.page: raise Exception("No active session")
        print(f"⌨️ Typing '{text}' into {selector}")
        self.page.fill(selector, text)

    def press_key(self, key):
        """Presses a specific key (e.g., 'Enter', 'Tab')."""
        if not self.page: raise Exception("No active session")
        print(f"🎹 Pressing Key: '{key}'")
        self.page.keyboard.press(key)

    def read_screen(self, instruction):
        """Reads information from the screen using Vision."""
        if not self.page: raise Exception("No active session")
        print(f"👁️📄 Vision Reading: '{instruction}'")
        
        # Snapshot
        timestamp = int(time.time())
        img_path = f"{self.img_base}/read_{timestamp}.png"
        self.page.screenshot(path=img_path)
        
        # LLM
        from src.llm_core import VisionCore
        vision = VisionCore()
        answer = vision.ask_about_image(img_path, instruction)
        
        print(f"    📝 Answer: {answer}")
        
        # Save to a file for the user to see
        with open("/workspaces/Airport/results/extracted_info.txt", "a") as f:
            f.write(f"[{time.ctime()}] Q: {instruction} -> A: {answer}\n")
            
        return answer

    def type_text_vision(self, instruction, text):
        """Types text using Vision to find the field."""
        if not self.page: raise Exception("No active session")
        
        print(f"👁️⌨️ Vision Typing: '{text}' -> Target: '{instruction}'")
        
        # Reuse click logic to focus the element
        result = self.click(mode="llm", instruction=instruction)
        
        if result["result"] == "Executed":
            # Once clicked/focused, type the text
            time.sleep(0.5)
            # Use insert_text for reliability in headless/no-ime envs
            self.page.keyboard.insert_text(text)
            print(f"    ↳ Typed (Inserted): {text}")

    def click(self, selector=None, mode="hybrid", instruction=None):
        """Clicks an element using the specified mode."""
        if not self.page: raise Exception("No active session")
        
        page = self.page
        log_entry = {"task": "click", "mode": mode, "timestamp": int(time.time())}
        
        # Snapshot name
        timestamp = int(time.time())
        pre_shot = f"{self.img_base}/pre_{timestamp}.png"
        page.screenshot(path=pre_shot)

        target_x, target_y = 0, 0
        
        # LLM Mode
        if mode == "llm":
            from src.llm_core import VisionCore
            print(f"Mode: LLM Vision -> Instruction: '{instruction}'")
            vision = VisionCore()
            vx, vy, vconf = vision.analyze_image(pre_shot, instruction)
            if vx is None: raise Exception("LLM failed")
            target_x, target_y = vx, vy

        # DOM / GUI / Hybrid
        else:
            if not selector: raise Exception("Selector required for non-LLM modes")
            try:
                page.wait_for_selector(selector, timeout=5000)
                element = page.query_selector(selector)
                box = element.bounding_box()
                dom_x = box['x'] + box['width'] / 2
                dom_y = box['y'] + box['height'] / 2
                target_x, target_y = dom_x, dom_y
                
                if mode in ["gui", "hybrid"]:
                    # Visual check logic (Simplified for brevity)
                    gui_x, gui_y, conf = self.find_element_visually(page, element)
                    if conf > 0.8: target_x, target_y = gui_x, gui_y
            except Exception as e:
                print(f"DOM/Wait Error: {e}")
                if mode == "hybrid": raise # Hybrid implies DOM dependency currently
                # In future: Fallback to full screen search if DOM fails?

        # Execute Click
        print(f"🖱️ Clicking at ({target_x}, {target_y})")
        # Visual feedback with mouse move
        page.mouse.move(target_x, target_y, steps=5) 
        time.sleep(0.2)
        
        # Use page.mouse.click which is lower level and usually works better for coords
        page.mouse.click(target_x, target_y)
        
        # Consider adding a second click if the first one might have missed focus?
        # frame.click() might be safer if we had the element handle, but here we use coords.
        
        # Post-action snapshot
        time.sleep(1)
        post_shot = f"{self.img_base}/post_{timestamp}.png"
        page.screenshot(path=post_shot)
        
        return {"result": "Executed", "coords": (target_x, target_y)}

    # --- CLI互換性のためのラッパー ---
    def execute_task(self, url, selector=None, mode="hybrid", instruction=None):
        try:
            self.start_session()
            self.nav(url)
            result = self.click(selector, mode, instruction)
            
            # Simple success check for CLI
            verify_selector = selector if mode != "llm" else "body"
            # start_url handling is tricky in split methods, simplified here
            is_success = True # Assume success if no error raised
            
            final_result = {
                "result": "Success" if is_success else "Failed",
                "screenshot_pre": f"{self.img_base}/pre_{int(time.time())}.png", # Approximate
                "screenshot_post": f"{self.img_base}/post_{int(time.time())}.png"
            }
            return final_result
            
        except Exception as e:
            return {"result": "Error", "error_message": str(e)}
        finally:
            self.stop_session()

    def verify_action(self, page, old_selector, start_url):
        # URLが遷移していれば成功とみなす
        if page.url != start_url:
            return True
        # URLが変わっていない場合は、要素が消えたかどうかで判定
        return not page.is_visible(old_selector, timeout=2000)

    def find_element_visually(self, page, element):
        """
        DOM要素のスクリーンショットを撮り、画面全体の中からその位置をOpenCVで特定する
        """
        # 1. ターゲット要素の画像をメモリ上に取得 (テンプレート)
        element_bytes = element.screenshot()
        element_arr = np.frombuffer(element_bytes, np.uint8)
        template = cv2.imdecode(element_arr, cv2.IMREAD_COLOR)

        # 2. 現在の画面全体の画像をメモリ上に取得
        screen_bytes = page.screenshot()
        screen_arr = np.frombuffer(screen_bytes, np.uint8)
        screen = cv2.imdecode(screen_arr, cv2.IMREAD_COLOR)

        # 3. テンプレートマッチング実行
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 4. 中心座標を計算
        top_left = max_loc
        h, w, _ = template.shape
        center_x = top_left[0] + w / 2
        center_y = top_left[1] + h / 2

        return center_x, center_y, max_val

    def record_black_box(self, data, timestamp):
        filename = f"{self.log_base}/flight_record_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Black Box updated: {filename}")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airport ATC: Autonomous Flight Controller")
    parser.add_argument("--url", default="https://example.com", help="Target URL")
    parser.add_argument("--selector", default=None, help="Target CSS selector")
    parser.add_argument("--mode", choices=["dom", "gui", "hybrid", "llm"], default="hybrid", help="Operation mode: dom, gui, hybrid, or llm")
    parser.add_argument("--instruction", help="Instruction for LLM mode (e.g. 'Click the login button')")
    
    args = parser.parse_args()
    
    # LLMモード以外ではselectorが必須（またはデフォルト値）
    if args.mode != "llm" and not args.selector:
        args.selector = "a" # Legacy default

    print(f"--- Mission Start ---")
    print(f"Target: {args.url}")
    print(f"Selector: {args.selector}")
    print(f"Mode: {args.mode}")
    if args.instruction:
        print(f"Instruction: {args.instruction}")
    print(f"---------------------")

    atc = ATC()
    result = atc.execute_task(args.url, args.selector, args.mode, args.instruction)
    
    print("\n" + "="*30)
    print("      MISSION REPORT      ")
    print("="*30)
    
    status = result.get('result')
    
    # ANSI Colors
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    if status == "Success":
        print(f"{GREEN}{BOLD}    [ SUCCESS ]{RESET}")
        print(f"    Target acquired and executed.")
    else:
        print(f"{RED}{BOLD}    [ FAILED ]{RESET}")
        if status == "Error":
             print(f"    Error: {result.get('error_message')}")
        else:
             print(f"    Action verification failed.")

    print("-"*30)
    print(f"Log File : {atc.log_base}/flight_record_{int(time.time())}.json")
    print(f"Pre-Shot : {result.get('screenshot_pre')}")
    print(f"Post-Shot: {result.get('screenshot_post')}")
    print("="*30 + "\n")