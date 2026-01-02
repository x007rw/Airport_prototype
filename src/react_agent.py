"""
ReAct Agent - Observe → Think → Act Loop
自律型エージェント：画面を見て、考えて、行動する
"""

import os
import time
import json
from datetime import datetime
from typing import Optional, Callable
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class ReActAgent:
    """
    ReAct (Reasoning + Acting) パターンを実装した自律型エージェント。
    
    ループ:
    1. Observe (観察): 現在の画面をキャプチャ
    2. Think (思考): AIが状況を分析し、次のアクションを決定
    3. Act (行動): 決定されたアクションを実行
    4. 繰り返し: ゴールに到達するまで
    """
    
    def __init__(self, atc, api_key: str = None):
        """
        Args:
            atc: ATC (Air Traffic Controller) インスタンス - 実際の操作を行う
            api_key: Google API Key
        """
        self.atc = atc
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.max_steps = 25  # 無限ループ防止
        self.collected_data = {}  # 収集したデータ（URL等）
        self.history = []  # 行動履歴
        self.screenshot_dir = "/workspaces/Airport/results/react_screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None
    
    def run(self, goal: str, on_step: Callable = None) -> dict:
        """
        ReActループを実行
        
        Args:
            goal: ユーザーが達成したいこと（自然言語）
            on_step: 各ステップ後に呼ばれるコールバック（進捗通知用）
        
        Returns:
            {
                "success": bool,
                "steps_taken": int,
                "history": list,
                "final_result": str
            }
        """
        print(f"\n{'='*50}")
        print(f"🎯 ReAct Agent Starting")
        print(f"   Goal: {goal}")
        print(f"{'='*50}\n")
        
        self.history = []
        step_count = 0
        
        try:
            # ブラウザセッション開始
            if not self.atc.page:
                self.atc.start_session()
            
            while step_count < self.max_steps:
                step_count += 1
                print(f"\n--- Step {step_count}/{self.max_steps} ---")
                
                # 1. OBSERVE: 画面をキャプチャ
                screenshot_path = self._capture_screen(step_count)
                print(f"👁️ Observed: {screenshot_path}")
                
                # 2. THINK: AIに次のアクションを決定させる
                thought = self._think(goal, screenshot_path, step_count)
                print(f"🧠 Thought: {thought.get('reasoning', 'No reasoning')}")
                print(f"📋 Action: {thought.get('action', 'unknown')} - {thought.get('params', {})}")
                
                # 履歴に追加
                self.history.append({
                    "step": step_count,
                    "timestamp": datetime.now().isoformat(),
                    "screenshot": screenshot_path,
                    "thought": thought
                })
                
                # コールバック通知
                if on_step:
                    on_step(step_count, thought, screenshot_path)
                
                # 3. CHECK: ゴール達成 or 完了判定
                if thought.get("action") == "done":
                    print(f"\n✅ Goal achieved!")
                    return {
                        "success": True,
                        "steps_taken": step_count,
                        "history": self.history,
                        "final_result": thought.get("result", "Task completed")
                    }
                
                if thought.get("action") == "fail":
                    print(f"\n❌ Agent determined task cannot be completed")
                    return {
                        "success": False,
                        "steps_taken": step_count,
                        "history": self.history,
                        "final_result": thought.get("reason", "Failed to complete task")
                    }
                
                # 4. ACT: アクションを実行
                self._act(thought)
                
                # アクションに応じた待機
                if thought.get("action") in ["goto", "click", "key"]:
                    time.sleep(2)  # ページ遷移を待つ
                else:
                    time.sleep(1)
            
            # 最大ステップ数到達
            print(f"\n⚠️ Max steps ({self.max_steps}) reached")
            return {
                "success": False,
                "steps_taken": step_count,
                "history": self.history,
                "final_result": "Max steps reached without completing goal"
            }
            
        except Exception as e:
            print(f"\n💥 Error: {e}")
            return {
                "success": False,
                "steps_taken": step_count,
                "history": self.history,
                "final_result": f"Error: {str(e)}"
            }
    
    def _capture_screen(self, step: int) -> str:
        """現在の画面をキャプチャ"""
        timestamp = int(time.time())
        path = f"{self.screenshot_dir}/step_{step}_{timestamp}.png"
        
        if self.atc.page:
            self.atc.page.screenshot(path=path)
        else:
            # PyAutoGUIでデスクトップ全体をキャプチャ
            import pyautogui
            pyautogui.screenshot(path)
        
        return path
    
    def _think(self, goal: str, screenshot_path: str, step: int) -> dict:
        """AIが画面を見て次のアクションを決定"""
        
        if not self.model:
            # Mock mode
            return self._mock_think(goal, step)
        
        # 過去の行動履歴をまとめる
        history_summary = self._format_history()
        
        prompt = f"""あなたは自律型GUIエージェントです。画面を見て、ゴールを達成するために次に何をすべきか決定してください。

## ゴール
「{goal}」

## これまでの行動履歴
{history_summary}

## 現在のステップ
{step}/{self.max_steps}

## 利用可能なアクション

1. **goto** - URLに移動
   - params: {{"url": "https://..."}}

2. **click** - 画面上の要素をクリック（座標指定）
   - params: {{"x": 100, "y": 200, "description": "何をクリックするか"}}

3. **type** - テキストを入力（現在フォーカスされている場所に）
   - params: {{"text": "入力するテキスト"}}

4. **key** - キーを押す
   - params: {{"key": "Enter" | "Tab" | "Escape" | "Backspace" など}}

5. **scroll** - スクロール
   - params: {{"direction": "up" | "down", "amount": 300}}

6. **wait** - 待機（ページ読み込みなど）
   - params: {{"seconds": 2}}

7. **read** - 画面から情報を読み取る（結果をメモする）
   - params: {{"target": "何を読み取るか", "result": "読み取った内容"}}

8. **get_url** - 現在のページのURLを取得してメモリに保存
   - params: {{"label": "保存する名前（例：product_url）"}}
   - 注意: これで取得したURLはsave_fileで使えます

9. **save_file** - テキストをファイルに直接保存（Linuxコマンド不要）
   - params: {{"filename": "results/output.txt", "content": "保存する内容", "append": true/false}}
   - 注意: get_urlで取得したURLを使う場合は content に "{{{{url:label}}}}" と書くと置換されます

10. **done** - ゴール達成、タスク完了
    - params: {{"result": "達成した結果の説明"}}

11. **fail** - タスク完了不可能と判断
    - params: {{"reason": "なぜ完了できないか"}}

## 出力形式
以下のJSON形式で出力してください。JSONのみを出力し、他の説明は不要です。

{{
    "observation": "現在の画面に何が見えるかの説明",
    "reasoning": "なぜこのアクションを選ぶのかの推論",
    "action": "アクション名",
    "params": {{...アクションのパラメータ...}}
}}

## 重要なルール
- 画像をよく見て、現在の状態を正確に把握してください
- clickの座標は画像の左上を(0,0)として指定してください
- **同じアクションを同じ座標で2回以上繰り返さないでください** - もしクリックが効かない場合は、別の座標を試すか、別のアプローチ（スクロール、キー操作など）を試してください
- 前のステップで画面が変わらなかった場合は、アクションが失敗しています。別の方法を試してください
- リンクをクリックする場合は、テキスト部分（青いリンク）を正確にクリックしてください
- ゴールに近づくための最短ルートを考えてください
- 迷ったらwaitして状況を観察してください
"""

        try:
            img = Image.open(screenshot_path)
            response = self.model.generate_content([prompt, img])
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
            
        except Exception as e:
            print(f"Think Error: {e}")
            return {
                "observation": "Error analyzing screen",
                "reasoning": f"Error: {str(e)}",
                "action": "wait",
                "params": {"seconds": 2}
            }
    
    def _act(self, thought: dict):
        """決定されたアクションを実行"""
        action = thought.get("action", "wait")
        params = thought.get("params", {})
        
        try:
            if action == "goto":
                url = params.get("url", "https://www.google.com")
                self.atc.nav(url)
                
            elif action == "click":
                x = params.get("x", 0)
                y = params.get("y", 0)
                if self.atc.page:
                    # クリック前に少し待つ
                    time.sleep(0.5)
                    self.atc.page.mouse.click(x, y)
                    # クリック後にページ遷移を待つ
                    time.sleep(1)
                else:
                    import pyautogui
                    pyautogui.click(x, y)
                print(f"   🖱️ Clicked at ({x}, {y})")
                
            elif action == "type":
                text = params.get("text", "")
                if self.atc.page:
                    self.atc.page.keyboard.insert_text(text)
                else:
                    import pyautogui
                    pyautogui.write(text, interval=0.05)
                print(f"   ⌨️ Typed: {text}")
                
            elif action == "key":
                key = params.get("key", "Enter")
                if self.atc.page:
                    self.atc.page.keyboard.press(key)
                else:
                    import pyautogui
                    pyautogui.press(key.lower())
                print(f"   🎹 Pressed: {key}")
                
            elif action == "scroll":
                direction = params.get("direction", "down")
                amount = params.get("amount", 300)
                if self.atc.page:
                    delta = -amount if direction == "up" else amount
                    self.atc.page.mouse.wheel(0, delta)
                else:
                    import pyautogui
                    scroll_amount = amount if direction == "up" else -amount
                    pyautogui.scroll(scroll_amount)
                print(f"   📜 Scrolled {direction} by {amount}px")
                
            elif action == "wait":
                seconds = params.get("seconds", 2)
                time.sleep(seconds)
                print(f"   ⏳ Waited {seconds}s")
                
            elif action == "read":
                target = params.get("target", "unknown")
                result = params.get("result", "")
                print(f"   👁️ Read '{target}': {result}")
                # 結果をファイルに保存
                with open("/workspaces/Airport/results/react_readings.txt", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] {target}: {result}\n")
                
            elif action == "get_url":
                label = params.get("label", "current_url")
                if self.atc.page:
                    url = self.atc.page.url
                    self.collected_data[label] = url
                    print(f"   🔗 Got URL [{label}]: {url}")
                else:
                    print(f"   ⚠️ No page available to get URL")
                
            elif action == "save_file":
                filename = params.get("filename", "results/output.txt")
                content = params.get("content", "")
                append = params.get("append", False)
                
                # URLプレースホルダーを置換
                for label, url in self.collected_data.items():
                    content = content.replace(f"{{{{url:{label}}}}}", url)
                    content = content.replace(f"{{url:{label}}}", url)  # 念のため両方対応
                
                # ファイルパスの処理
                if not filename.startswith("/"):
                    filename = f"/workspaces/Airport/{filename}"
                
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                mode = "a" if append else "w"
                with open(filename, mode, encoding="utf-8") as f:
                    f.write(content + "\n")
                print(f"   💾 Saved to {filename}: {content[:50]}...")
                
        except Exception as e:
            print(f"   ⚠️ Action Error: {e}")
    
    def _format_history(self) -> str:
        """履歴をテキストにフォーマット"""
        if not self.history:
            return "(まだ行動していません)"
        
        lines = []
        for h in self.history[-5:]:  # 直近5ステップ
            thought = h.get("thought", {})
            lines.append(f"Step {h['step']}: {thought.get('action', '?')} - {thought.get('observation', '')[:100]}")
        
        return "\n".join(lines)
    
    def _mock_think(self, goal: str, step: int) -> dict:
        """Mock mode for testing"""
        if step == 1:
            return {
                "observation": "Mock: Starting browser",
                "reasoning": "First, navigate to the target site",
                "action": "goto",
                "params": {"url": "https://www.google.com"}
            }
        elif step == 2:
            return {
                "observation": "Mock: On Google homepage",
                "reasoning": "Need to search for the goal",
                "action": "type",
                "params": {"text": goal}
            }
        elif step == 3:
            return {
                "observation": "Mock: Text entered",
                "reasoning": "Press Enter to search",
                "action": "key",
                "params": {"key": "Enter"}
            }
        elif step == 4:
            return {
                "observation": "Mock: Search results visible",
                "reasoning": "Goal appears to be achieved",
                "action": "done",
                "params": {"result": f"Searched for: {goal}"}
            }
        else:
            return {
                "observation": "Mock: Unknown state",
                "reasoning": "Ending mock session",
                "action": "done",
                "params": {"result": "Mock completed"}
            }


# スタンドアロン実行用
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/workspaces/Airport')
    from src.main import ATC
    
    goal = sys.argv[1] if len(sys.argv) > 1 else "Googleで東京の天気を検索して"
    
    atc = ATC()
    agent = ReActAgent(atc)
    
    try:
        result = agent.run(goal)
        print("\n" + "="*50)
        print("📊 Final Report")
        print("="*50)
        print(f"Success: {result['success']}")
        print(f"Steps: {result['steps_taken']}")
        print(f"Result: {result['final_result']}")
    finally:
        atc.stop_session()
