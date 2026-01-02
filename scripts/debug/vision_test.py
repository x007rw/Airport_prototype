from main import ATC
import time

def run_vision_test():
    print("🚀 Starting VISION ONLY Test Method")
    atc = ATC()
    
    try:
        # Start
        atc.start_session()
        atc.nav("https://www.saucedemo.com/")
        
        # Extra wait for initial load & render
        print("⏳ Waiting 5 seconds for render...")
        time.sleep(5)
        
        # FORCE REFRESH to ensure render?
        # atc.page.reload()
        # time.sleep(3)

        # 1. Username (DOM Verification)
        print("\n--- 1. Input Username (DOM) ---")
        atc.type_text("#user-name", "standard_user")
        
        # 2. Password (DOM Verification)
        print("\n--- 2. Input Password (DOM) ---")
        atc.type_text("#password", "secret_sauce")
        
        # 3. Click Login (DOM Verification)
        print("\n--- 3. Click Login (DOM) ---")
        atc.click("#login-button", mode="dom")
        
        print("⏳ Waiting 5 seconds for login transition...")
        time.sleep(5) # Wait for page transition
        
        # 4. Select Item
        print("\n--- 4. Select Backpack ---")
        atc.click(mode="llm", instruction="Click the text 'Sauce Labs Backpack'")
        
        print("⏳ Waiting 3 seconds for item page...")
        time.sleep(3)

        # 5. Add to cart
        print("\n--- 5. Add to Cart ---")
        atc.click(mode="llm", instruction="Click the 'Add to cart' button")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        atc.stop_session()

if __name__ == "__main__":
    run_vision_test()
