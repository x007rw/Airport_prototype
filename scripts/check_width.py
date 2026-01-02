from playwright.sync_api import sync_playwright
import time

def check_layout():
    print("🔍 Inspecting Cockpit Layout Dimensions...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a standard 1920x1080 viewport
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            page.goto("http://localhost:3000", timeout=10000)
            time.sleep(2) # Wait for rendering
            
            # Select the main container and sections
            # We assume the structure is main > section (left) + section (right)
            
            main_width = page.evaluate("document.querySelector('main').getBoundingClientRect().width")
            
            # Get Left Section
            left_width = page.evaluate("document.querySelector('main > section:first-child').getBoundingClientRect().width")
            
            # Get Right Section
            right_width = page.evaluate("document.querySelector('main > section:last-child').getBoundingClientRect().width")
            
            print(f"🖥️  Viewport Width: 1920px")
            print(f"📊 Main Container Width: {main_width}px")
            print(f"👈 Left Panel Width: {left_width}px ({left_width/main_width*100:.2f}%)")
            print(f"👉 Right Panel Width: {right_width}px ({right_width/main_width*100:.2f}%)")
            
            if abs(left_width - right_width) < 2:
                print("✅ PERFECT SPLIT (Target achieved)")
            else:
                print("❌ IMBALANCED SPLIT")

            # Take a screenshot for visual proof
            page.screenshot(path="/workspaces/Airport/results/layout_check.png")
            print("📸 Screenshot saved to results/layout_check.png")
            
        except Exception as e:
            print(f"⚠️ Error measuring layout: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_layout()
