import yaml
import time
import argparse
from .main import ATC

def run_workflow(yaml_path):
    print(f"✈️ Loading Flight Plan: {yaml_path}")
    
    with open(yaml_path, 'r') as f:
        plan = yaml.safe_load(f)
        
    atc = ATC()
    
    for task in plan.get("tasks", []):
        print(f"\n🔹 Executing Task: {task.get('name')}")
        
        # Start persistent session for this task
        atc.start_session()
        
        try:
            for i, step in enumerate(task.get("steps", [])):
                action = step.get("action")
                print(f"  Step {i+1}: {action}")
                
                try:
                    if action == "goto":
                        atc.nav(step.get("url"))

                    elif action == "click":
                        atc.click(
                            selector=step.get("selector"),
                            mode=step.get("mode", "hybrid"),
                            instruction=step.get("instruction")
                        )
                        
                    elif action == "type":
                        atc.type_text(
                            selector=step.get("selector"),
                            text=step.get("text")
                        )
                    
                    elif action == "type_vision":
                        atc.type_text_vision(
                            instruction=step.get("instruction"),
                            text=step.get("text")
                        )
                    
                    elif action == "key":
                        atc.press_key(step.get("key"))
                    
                    elif action == "read":
                        atc.read_screen(step.get("instruction"))
                        
                    elif action == "wait":
                        time.sleep(step.get("seconds", 1))

                except Exception as e:
                    print(f"    ❌ Step Failed: {e}")
                    # Decide whether to break or continue based on config?
                    # For now, we break the task.
                    break
        finally:
            atc.stop_session()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", help="Path to flight_plan.yaml")
    args = parser.parse_args()
    
    run_workflow(args.plan)
