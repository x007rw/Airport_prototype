from playwright.sync_api import sync_playwright
import time
import sys

def debug_cockpit():
    print("🕵️ Debugging Airport Cockpit...")
    
    with sync_playwright() as p:
        # Browser setup
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        try:
            # 1. Access Page
            print("🌐 Navigating to http://localhost:3000...")
            page.goto("http://localhost:3000", timeout=15000)
            page.wait_for_load_state("networkidle")
            time.sleep(3) # Wait for hydration

            # 2. Check Welcome Message (Japanese)
            # Look for the specific Japanese greeting
            content = page.content()
            welcome_msg = "機長"
            
            if welcome_msg in content:
                print(f"✅ Text Check Passed: Found '{welcome_msg}'")
            else:
                print("❌ Text Check Failed: Japanese welcome message NOT found.")
                # Extract what IS prominent
                # Try to find the chat bubble text
                bubbles = page.locator(".bg-gray-900").all_text_contents()
                print(f"   Current Chat Bubbles: {bubbles}")

            # 3. Check Layout (50/50 Split)
            try:
                main_width = page.evaluate("document.querySelector('main').getBoundingClientRect().width")
                left_width = page.evaluate("document.querySelector('main > section:first-child').getBoundingClientRect().width")
                ratio = left_width / main_width * 100
                
                print(f"📏 Layout Check: Left Panel is {ratio:.2f}% of screen.")
                if 49.0 <= ratio <= 51.0:
                    print("✅ Layout Check Passed: Perfectly balanced.")
                else:
                    print("❌ Layout Check Failed: Left panel width is incorrect.")
            except Exception as e:
                 print(f"⚠️ Layout Measure Error: {e}")

            # 4. Screenshot Evidence
            page.screenshot(path="/workspaces/Airport/results/debug_screenshot.png")
            print("📸 Evidence saved to results/debug_screenshot.png")

        except Exception as e:
            print(f"🔥 Critical Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_cockpit()
