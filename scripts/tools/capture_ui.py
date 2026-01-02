from playwright.sync_api import sync_playwright
import time

def capture_cockpit():
    print("📸 Capturing Airport Cockpit UI...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        # Navigate to Cockpit
        page.goto("http://localhost:3000")
        time.sleep(5)  # Wait for hydration
        
        # Screenshot Dashboard
        page.screenshot(path="/workspaces/Airport/results/cockpit_dashboard.png")
        print("✅ Dashboard screenshot saved")
        
        # Click Flight Recorder tab if exists
        try:
            page.click("text=Flight Recorder", timeout=3000)
            time.sleep(2)
            page.screenshot(path="/workspaces/Airport/results/cockpit_videos.png")
            print("✅ Videos tab screenshot saved")
        except:
            print("⚠️ Flight Recorder tab not found or not clickable")
        
        browser.close()
        print("📸 Capture complete!")

if __name__ == "__main__":
    capture_cockpit()
