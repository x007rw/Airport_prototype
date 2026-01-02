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
            self.model = genai.GenerativeModel('gemini-3-flash-preview')

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

    def generate_plan(self, user_instruction: str) -> dict:
        """
        Generates a flight plan from a natural language instruction.
        Returns a dictionary with 'plan' (list of steps) and 'summary'.
        """
        import time
        
        if not self.api_key:
            # Mock mode for testing
            return {
                "summary": f"Mock plan for: {user_instruction}",
                "plan": [
                    {"step": 1, "action": "goto", "url": "https://www.google.com"},
                    {"step": 2, "action": "type_vision", "instruction": "検索ボックス", "text": user_instruction},
                    {"step": 3, "action": "key", "key": "Enter"},
                    {"step": 4, "action": "wait", "seconds": 2},
                    {"step": 5, "action": "read", "instruction": "検索結果の内容を読み取ってください"}
                ]
            }

        prompt = f"""あなたは Airport システムのフライトプランナーです。
ユーザーからの指示を、以下の利用可能なアクションのみを使って具体的なステップに分解してください。

## 利用可能なアクション

1. **goto** - URLに移動
   - パラメータ: url (string)
   - 例: {{"action": "goto", "url": "https://www.google.com"}}

2. **click** - 要素をクリック (セレクタ指定)
   - パラメータ: selector (CSS selector), mode (optional: "dom", "hybrid")
   - 例: {{"action": "click", "selector": "#search-btn"}}

3. **click_vision** - 要素をクリック (Vision AI で検出)
   - パラメータ: instruction (何をクリックするかの説明)
   - 例: {{"action": "click_vision", "instruction": "検索ボタンをクリック"}}

4. **type** - テキストを入力 (セレクタ指定)
   - パラメータ: selector, text
   - 例: {{"action": "type", "selector": "input[name='q']", "text": "東京の天気"}}

5. **type_vision** - テキストを入力 (Vision AI で検出)
   - パラメータ: instruction, text
   - 例: {{"action": "type_vision", "instruction": "検索ボックス", "text": "東京の天気"}}

6. **key** - キーを押す
   - パラメータ: key (Enter, Tab, Escape など)
   - 例: {{"action": "key", "key": "Enter"}}

7. **read** - 画面から情報を読み取る
   - パラメータ: instruction
   - 例: {{"action": "read", "instruction": "現在の気温を読み取ってください"}}

8. **wait** - 指定秒数待機
   - パラメータ: seconds
   - 例: {{"action": "wait", "seconds": 2}}

9. **launch_app** - デスクトップアプリを起動 (Linuxのみ)
   - パラメータ: command
   - 例: {{"action": "launch_app", "command": "mousepad"}}

## ユーザーの指示
「{user_instruction}」

## 出力形式
以下のJSON形式で出力してください。JSONのみを出力し、他の説明は不要です。

{{
    "summary": "このミッションの簡潔な説明（日本語）",
    "plan": [
        {{"step": 1, "action": "アクション名", ...パラメータ}},
        {{"step": 2, "action": "アクション名", ...パラメータ}},
        ...
    ]
}}
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.strip()
                
                # Extract JSON from response
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                plan_data = json.loads(text)
                return plan_data
                
            except Exception as e:
                print(f"Plan Generation Error (Attempt {attempt+1}/{max_retries}): {e}")
                if "429" in str(e) or "Resource exhausted" in str(e):
                    time.sleep((attempt + 1) * 5)
                else:
                    time.sleep(2)
        
        # Fallback
        return {
            "summary": "プラン生成に失敗しました",
            "plan": [],
            "error": "Failed to generate plan after retries"
        }


class Attendant:
    """
    会話型AIアシスタント。ユーザーの意図を判断し、適切に応答する。
    - 質問 → 回答
    - タスク依頼 → フライトプラン生成
    - 曖昧な指示 → 確認を求める
    - 雑談 → 自然に応答
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.conversation_history = []
        self.pending_plan = None
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None
    
    def chat(self, user_message: str) -> dict:
        """
        ユーザーのメッセージを処理し、適切な応答を返す。
        
        Returns: {
            "response": str,           # Attendantの応答テキスト
            "intent": str,             # "task", "question", "confirmation", "chat"
            "plan": dict | None,       # タスクの場合はフライトプラン
            "needs_confirmation": bool # ユーザーの確認が必要か
        }
        """
        import time
        
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        if not self.api_key:
            # Mock mode
            return self._mock_response(user_message)
        
        # Build conversation context
        history_text = self._format_history()
        
        prompt = f"""あなたは Airport システムの「Attendant（アテンダント）」です。
パイロット（ユーザー）をサポートする優秀なアシスタントとして、自然で親しみやすい会話をしてください。

## あなたの役割
1. **タスク依頼の場合**: ブラウザやデスクトップを操作するタスクを依頼された場合、フライトプランを生成します。
2. **質問の場合**: 知識に基づいて回答します（ただしリアルタイム情報は持っていないことを伝えます）。
3. **曖昧な指示の場合**: 詳細を確認する質問をします。
4. **雑談の場合**: フレンドリーに応答しますが、本来の業務に戻るよう促します。
5. **確認への応答**: 「はい」「OK」「お願い」などの確認は、保留中のタスクの実行許可とみなします。

## 会話履歴
{history_text}

## 現在のユーザー入力
「{user_message}」

## 出力形式
以下のJSON形式で出力してください。JSONのみを出力し、他の説明は不要です。

{{
    "response": "ユーザーへの応答テキスト（日本語、フレンドリーに）",
    "intent": "task" | "question" | "confirmation" | "chat" | "clarification",
    "needs_confirmation": true | false,
    "task_description": "タスクの場合、具体的に何をするかの説明（タスク以外はnull）"
}}

## 重要なルール
- intentが"task"の場合、needs_confirmationはtrueにしてください（ユーザーの承認を得てから実行）
- intentが"confirmation"の場合、ユーザーが以前提案したタスクを承認したことを意味します
- 曖昧な指示（例：「あれやって」「いい感じに」）には、intentを"clarification"にして詳細を聞いてください
- 会話履歴を参照して、文脈に沿った応答をしてください
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                text = response.text.strip()
                
                # Extract JSON
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(text)
                
                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": result.get("response", "")
                })
                
                # If it's a task, generate the flight plan
                if result.get("intent") == "task" and result.get("task_description"):
                    vision = VisionCore(self.api_key)
                    plan = vision.generate_plan(result["task_description"])
                    result["plan"] = plan
                    self.pending_plan = plan
                elif result.get("intent") == "confirmation" and self.pending_plan:
                    # User confirmed, return the pending plan
                    result["plan"] = self.pending_plan
                    result["execute_now"] = True
                
                return result
                
            except Exception as e:
                print(f"Attendant Error (Attempt {attempt+1}/{max_retries}): {e}")
                if "429" in str(e) or "Resource exhausted" in str(e):
                    time.sleep((attempt + 1) * 5)
                else:
                    time.sleep(2)
        
        # Fallback
        return {
            "response": "申し訳ありません、一時的にシステムに問題が発生しています。もう一度お試しください。",
            "intent": "error",
            "plan": None,
            "needs_confirmation": False
        }
    
    def _format_history(self, max_turns=10) -> str:
        """会話履歴をフォーマット"""
        recent = self.conversation_history[-max_turns*2:]
        lines = []
        for msg in recent:
            role = "パイロット" if msg["role"] == "user" else "Attendant"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines) if lines else "(会話開始)"
    
    def _mock_response(self, user_message: str) -> dict:
        """API キーがない場合のモック応答"""
        lower = user_message.lower()
        
        # Simple intent detection for mock
        if any(word in lower for word in ["調べて", "検索", "開いて", "行って", "クリック", "入力", "探して"]):
            self.pending_plan = {
                "summary": f"Mock: {user_message}",
                "plan": [
                    {"step": 1, "action": "goto", "url": "https://www.google.com"},
                    {"step": 2, "action": "type_vision", "instruction": "検索ボックス", "text": user_message},
                    {"step": 3, "action": "key", "key": "Enter"},
                    {"step": 4, "action": "read", "instruction": "結果を読み取る"}
                ]
            }
            return {
                "response": f"了解しました。「{user_message}」のフライトプランを作成しました。右側のMission Planタブで確認してください。実行してよろしければ「OK」と言ってください。",
                "intent": "task",
                "plan": self.pending_plan,
                "needs_confirmation": True
            }
        elif any(word in lower for word in ["はい", "ok", "お願い", "実行", "やって", "いいよ", "頼む"]):
            if self.pending_plan:
                return {
                    "response": "承知しました！ミッションを開始します。シートベルトをお締めください。🚀",
                    "intent": "confirmation",
                    "plan": self.pending_plan,
                    "execute_now": True,
                    "needs_confirmation": False
                }
        elif "?" in user_message or any(word in lower for word in ["とは", "って何", "教えて", "なに", "どう"]):
            return {
                "response": "ご質問ありがとうございます。私はリアルタイムの情報は持っていませんが、ウェブで調べることはできます。「〇〇を調べて」と言っていただければ、代わりに検索いたします。",
                "intent": "question",
                "plan": None,
                "needs_confirmation": False
            }
        else:
            return {
                "response": f"「{user_message}」についてですね。具体的にどのような操作をご希望ですか？例えば「〇〇を検索して」「〇〇のページを開いて」のように指示していただけると、フライトプランを作成できます。",
                "intent": "clarification",
                "plan": None,
                "needs_confirmation": False
            }
    
    def clear_history(self):
        """会話履歴をクリア"""
        self.conversation_history = []
        self.pending_plan = None
