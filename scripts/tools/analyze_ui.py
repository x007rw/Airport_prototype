import sys
sys.path.append(".")

from src.llm_core import VisionCore
import json

def analyze_ui():
    vision = VisionCore()
    
    # Analyze Dashboard
    print("=" * 60)
    print("📊 DASHBOARD ANALYSIS")
    print("=" * 60)
    dashboard_analysis = vision.ask_about_image(
        "/workspaces/Airport/results/cockpit_dashboard.png",
        """Analyze this web application dashboard UI screenshot in detail.
        Describe:
        1. Overall layout (sidebar, main content, etc.)
        2. Color scheme and design aesthetic
        3. All visible text and button labels
        4. Navigation elements
        5. Any status indicators
        6. Quality assessment: Is this a modern, premium-looking UI? Rate 1-10.
        7. Any issues or improvements needed?
        Respond in English."""
    )
    print(dashboard_analysis)
    
    # Analyze Videos Tab
    print("\n" + "=" * 60)
    print("🎬 FLIGHT RECORDER (VIDEOS) ANALYSIS")
    print("=" * 60)
    videos_analysis = vision.ask_about_image(
        "/workspaces/Airport/results/cockpit_videos.png",
        """Analyze this web application video gallery UI screenshot.
        Describe:
        1. Layout structure
        2. List of recordings shown (if any)
        3. Video player area
        4. Design consistency with a dark/tech theme
        5. Quality assessment: Rate 1-10.
        Respond in English."""
    )
    print(videos_analysis)
    
    return {
        "dashboard": dashboard_analysis,
        "videos": videos_analysis
    }

if __name__ == "__main__":
    result = analyze_ui()
    
    # Save to file
    with open("/workspaces/Airport/results/ui_analysis.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("\n✅ Analysis saved to results/ui_analysis.json")
