import sys
import os
import argparse

# Add src to python path so we can import modules from it
sys.path.append(os.path.join(os.getcwd(), "src"))

from src import autopilot
from src import desktop_controller

def run_web(args):
    # シナリオファイルのパス解決
    scenario_path = args.scenario
    if not os.path.exists(scenario_path):
        # try in scenarios/ folder
        alt_path = os.path.join("scenarios", scenario_path)
        if os.path.exists(alt_path):
            scenario_path = alt_path
        else:
            print(f"Error: Scenario file not found: {scenario_path}")
            return

    print(f"✈️ Running Web Scenario: {scenario_path}")
    autopilot.run_workflow(scenario_path)

def run_desktop(args):
    print("🖥️ Running Desktop Demo")
    desktop_controller.run_desktop_demo()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airport Automation Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Mode of operation")

    # Web Autopilot
    web_parser = subparsers.add_parser("web", help="Run web automation scenario")
    web_parser.add_argument("scenario", help="Path to YAML scenario file (e.g. test_scenarios.yaml)")
    
    # Desktop
    desktop_parser = subparsers.add_parser("desktop", help="Run desktop automation demo")

    args = parser.parse_args()

    if args.command == "web":
        run_web(args)
    elif args.command == "desktop":
        run_desktop(args)
    else:
        parser.print_help()
