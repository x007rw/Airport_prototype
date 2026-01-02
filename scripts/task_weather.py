import sys
import os
import time
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.main import ATC
from src.desktop_controller import DesktopATC

def mission_weather_report():
    print("\n🚀 MISSION START: Web to Desktop Weather Report\n")
    
    # --- PHASE 1: Web Information Retrieval ---
    print("--- [Phase 1] Web Search ---")
    web_atc = ATC()
    web_atc.start_session()
    
    try:
        # Search
        web_atc.nav("https://duckduckgo.com/")
        time.sleep(3)
        
        web_atc.type_text_vision(
            instruction="Click the search input box", 
            text="Tokyo Weather"
        )
        web_atc.press_key("Enter")
        time.sleep(5)
        
        # Read Info
        question = "What is the current temperature and weather condition in Tokyo?"
        weather_info = web_atc.read_screen(question)
        print(f"\n🌤️ Acquired Info: {weather_info}\n")
        
    finally:
        web_atc.stop_session()

    if not weather_info or "fail" in weather_info.lower() or "cannot" in weather_info.lower():
        print("❌ Failed to get weather info. Aborting Phase 2.")
        return

    # --- PHASE 2: Desktop Recording ---
    print("--- [Phase 2] Desktop Recording ---")
    desktop = DesktopATC()
    
    # Launch Editor
    desktop.launch_app("mousepad &")
    
    # Wait for window
    time.sleep(3)
    
    # Focus and Type
    desktop.type_vision("Click the white text editing area", f"Tokyo Weather Report\n--------------------\n{weather_info}\n")
    desktop.press_key("enter")
    desktop.press_key("enter")
    
    timestamp = time.ctime()
    desktop.type_vision("Click the text area", f"Recorded at: {timestamp}\nby Airport Agent")
    
    time.sleep(2)
    
    # Save File
    print("💾 Saving file...")
    desktop.press_hotkey("ctrl", "s")
    time.sleep(2)
    
    # Save Dialog handling
    # Dialog usually focuses on filename input automatically
    filename = f"/workspaces/Airport/results/weather_{int(time.time())}.txt"
    # PyAutoGUI write is safer for system dialogs than vision clicking inputs
    import pyautogui
    pyautogui.write(filename, interval=0.1)
    time.sleep(1)
    desktop.press_key("enter")
    
    time.sleep(2)
    
    # Close App
    desktop.press_hotkey("ctrl", "q") # Quit shortcut for most Linux apps
    
    print("\n✅ MISSION COMPLETE\n")

if __name__ == "__main__":
    mission_weather_report()
