import pyautogui
import time
import os
import subprocess
from dotenv import load_dotenv
from src.llm_core import VisionCore

load_dotenv()

class DesktopATC:
    def __init__(self):
        pyautogui.FAILSAFE = False
        # Xvfb環境ではスクリーンショットのためにDISPLAY環境変数が重要
        self.img_base = "/workspaces/Airport/results/desktop_screenshots"
        self.log_base = "/workspaces/Airport/results/desktop_logs"
        os.makedirs(self.img_base, exist_ok=True)
        os.makedirs(self.log_base, exist_ok=True)
        self.vision = VisionCore()

    def launch_app(self, command):
        """Launches a desktop application."""
        print(f"🖥️ Launching App: {command}")
        subprocess.Popen(command, shell=True)
        time.sleep(3) # Wait for app to open

    def capture_screen(self, prefix="shot"):
        """Captures the entire desktop."""
        timestamp = int(time.time())
        path = f"{self.img_base}/{prefix}_{timestamp}.png"
        
        # PyAutoGUI screenshot
        # Note: In some headless environments, pyautogui.screenshot() might capture a black screen.
        # If that happens, we might need 'scrot'. Let's try pyautogui first.
        try:
            pyautogui.screenshot(path)
        except Exception as e:
            print(f"⚠️ PyAutoGUI screenshot failed: {e}. Trying scrot...")
            subprocess.run(["scrot", path])
            
        return path

    def click_vision(self, instruction):
        """Finds an element using Vision and clicks it."""
        print(f"👁️ Vision Click: '{instruction}'")
        
        # 1. Capture Screen
        img_path = self.capture_screen("pre")
        
        # 2. Analyze
        x, y, conf = self.vision.analyze_image(img_path, instruction)
        
        if x is None:
            print("❌ Vision failed to find target.")
            return False
            
        print(f"    ↳ Coords: ({x}, {y}) Conf: {conf}")

        # 3. Click
        # Move mouse smoothly for visual debugging (if watching VNC)
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click(x, y)
        
        # 4. Post-action screenshot
        time.sleep(1)
        self.capture_screen("post")
        return True

    def type_vision(self, instruction, text):
        """Clicks a field and types text."""
        print(f"👁️⌨️ Vision Type: '{text}' -> Target: '{instruction}'")
        
        if self.click_vision(instruction):
            time.sleep(0.5)
            # Clear field? Ctrl+A -> Backspace is standard, but app dependent.
            # For now, just type.
            pyautogui.write(text, interval=0.1)
            return True
        return False

    def press_key(self, key):
        print(f"🎹 Pressing Key: {key}")
        pyautogui.press(key)

    def press_hotkey(self, *args):
        print(f"🎹 Pressing Hotkey: {' + '.join(args)}")
        pyautogui.hotkey(*args)

def run_desktop_demo():
    atc = DesktopATC()
    
    # --- Scenario 1: Calculator (galculator) ---
    print("\n=== 1. Calculator Demo ===")
    atc.launch_app("galculator &")
    
    # 1 + 2 = 
    atc.click_vision("Click the button labeled '1'")
    atc.click_vision("Click the plus sign '+' button")
    atc.click_vision("Click the button labeled '2'")
    atc.click_vision("Click the equals '=' button")
    
    time.sleep(2)
    
    # Close calculator? Or just leave it open.
    # Let's close it using vision
    atc.click_vision("Click the close window button (X) usually in top right corner of the window")
    time.sleep(1)

    # --- Scenario 2: Text Editor (mousepad) ---
    print("\n=== 2. Text Editor Demo ===")
    atc.launch_app("mousepad &")
    
    atc.type_vision("Click the main white text editing area", "Hello from Airport Vision Agent!")
    atc.press_key("enter")
    atc.type_vision("Click the text editing area again", "This is running on a Linux Desktop.")
    
    time.sleep(2)
    
    # Save (Ctrl+S) using keyboard, then handle dialog with vision
    # atc.vision_key("ctrl", "s") ... simplified to just closing for now
    atc.click_vision("Click the close window button (X)")
    
    # Handle "Do you want to save?" dialog if it appears
    # "Don't Save" button
    atc.click_vision("Click the 'Don't Save' or 'Discard' button if a dialog appears")

if __name__ == "__main__":
    run_desktop_demo()
