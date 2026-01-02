import google.generativeai as genai
from PIL import Image
import os
import json

class VisionCore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("⚠️ Warning: GOOGLE_API_KEY is not set. LLM mode will run in Mock mode.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze_image(self, image_path, instruction):
        """
        Sends the image to Gemini 2.0 Flash to find the coordinates of the target element.
        Returns: (x, y, confidence)
        """
        if not self.api_key:
            print("[LLM Mock] Pretending to see the image...")
            return 100, 100, 0.5

        import time
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                
                prompt = f"""
                You are an intelligent GUI automation agent.
                Look at the attached screenshot of a web page/application.
                Your task is to identify the UI element that matches this user instruction: "{instruction}".
                
                Return the center coordinates (x, y) of that element in the image.
                The coordinates must be precise integers, relative to the top-left image corner (0,0).
                
                Output strictly valid JSON only:
                {{
                    "x": 123,
                    "y": 456,
                    "confidence": 0.95
                }}
                """

                response = self.model.generate_content([prompt, img])
                
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                data = json.loads(text)
                return data["x"], data["y"], data.get("confidence", 1.0)

            except Exception as e:
                wait_time = (attempt + 1) * 5  # 5s, 10s, 15s wait
                print(f"LLM Error (Attempt {attempt+1}/{max_retries}): {e}")
                if "429" in str(e) or "Resource exhausted" in str(e):
                    print(f"⚠️ Rate limit hit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # For other errors, maybe wait less or break? 
                    # Let's retry anyway for robustness
                    time.sleep(2)
        
        return None, None, 0.0

    def ask_about_image(self, image_path, question):
        """
        Asks a question about the image and returns the text answer.
        """
        if not self.api_key:
            return "Mock Answer: 012-3456-7890"

        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                prompt = f"""
                Look at the screenshot.
                Answer the following question based on the visual information: "{question}"
                
                Return ONLY the answer text. Be concise.
                """
                response = self.model.generate_content([prompt, img])
                return response.text.strip()
            except Exception as e:
                print(f"LLM Extract Error: {e}")
                time.sleep(3)
        return "Failed to extract"


