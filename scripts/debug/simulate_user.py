from playwright.sync_api import sync_playwright
import time
import os

def run_user_simulation():
    print("👨‍✈️ Captain AI initializing...")
    print("🚀 Mission: Test Airport Cockpit Functionality E2E")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use large viewport to simulate desktop
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            # 1. Access Cockpit
            print("\n[Step 1] Accessing Cockpit...")
            page.goto("http://localhost:3000")
            page.wait_for_selector("text=機長", timeout=10000)
            print("✅ Access confirmed. Attendant is ready.")

            # 2. Input Order
            print("\n[Step 2] Sending Orders...")
            # Type in the input field
            page.fill("input[placeholder='Describe your mission...']", "東京の天気を調べて記録してください")
            time.sleep(1)
            # Click send button
            page.click("button >> canvas, svg, .lucide-send") # Send icon is typically the button
            # Or reliable selector:
            page.keyboard.press("Enter")
            print("✅ Order sent: '東京の天気を調べて記録してください'")

            # 3. Wait for Attendant Response
            print("\n[Step 3] Waiting for Planning...")
            # Wait for the "Drafting..." indicator to disappear and new message to appear
            time.sleep(3) 
            page.wait_for_selector("text=了解いたしました", timeout=10000)
            print("✅ Plan approved by Attendant.")

            # 4. Take-off
            print("\n[Step 4] Initiating Take-off sequence...")
            # Click the big TAKE-OFF button
            page.click("text=TAKE-OFF")
            print("🚀 TAKE-OFF! Mission started.")

            # 5. Monitor Execution (Wait for completion)
            print("\n[Step 5] Monitoring flight status...")
            # Switch to 'Mission Plan' tab to see updates
            page.click("text=Mission Plan")
            
            # Monitoring loop
            max_wait = 60 # seconds
            for i in range(max_wait):
                # Check for logs in the terminal area
                logs = page.locator("div.flex-grow.overflow-y-auto").text_content()
                
                if "MISSION COMPLETE" in logs or "ミッションを開始します" in logs:
                     print(f"📡 Telemetry received (T+{i}s)")
                
                # Check execution status (assuming the button changes or logs update)
                if i % 10 == 0:
                    page.screenshot(path=f"/workspaces/Airport/results/flight_status_{i}s.png")
                    print(f"📸 Snapshot taken at T+{i}s")

                time.sleep(1)

            print("✅ Simulation sequence finished.")
            
        except Exception as e:
            print(f"🔥 Mission Failure: {e}")
            page.screenshot(path="/workspaces/Airport/results/failure_state.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_user_simulation()
