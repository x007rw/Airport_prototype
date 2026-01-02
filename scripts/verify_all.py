import subprocess
import sys
import time

def run_test(mode, url="https://example.com", selector="a"):
    print(f"\n🚀 Testing Mode: {mode.upper()} ...")
    start_time = time.time()
    
    cmd = [sys.executable, "main.py", "--url", url, "--selector", selector, "--mode", mode]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    # Check if "SUCCESS" is in the output (since main.py prints [ SUCCESS ])
    is_success = "[ SUCCESS ]" in result.stdout
    
    if is_success:
        print(f"✅ {mode.upper()} Mode: PASSED ({elapsed:.2f}s)")
    else:
        print(f"❌ {mode.upper()} Mode: FAILED")
        print("--- STDERR ---")
        print(result.stderr)
        print("--- STDOUT ---")
        print(result.stdout)
        
    return is_success

def main():
    print("========================================")
    print("      AIRPORT SYSTEM VERIFICATION       ")
    print("========================================")
    
    modes = ["dom", "gui", "hybrid"]
    results = {}
    
    for mode in modes:
        results[mode] = run_test(mode)
        time.sleep(1) # Interval
        
    print("\n========================================")
    print("           FINAL RESULTS                ")
    print("========================================")
    
    all_passed = True
    for mode, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        icon = "✅" if passed else "❌"
        print(f"{icon} {mode.ljust(8)} : {status}")
        if not passed:
            all_passed = False
            
    print("========================================")
    
    if all_passed:
        print("🎉 ALL SYSTEMS GO! Ready for flight.")
        sys.exit(0)
    else:
        print("⚠️ Some systems failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()
