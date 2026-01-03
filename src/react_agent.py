"""
ReAct Agent - Observe → Think → Act Loop
自律型エージェント：画面を見て、考えて、行動する
"""

import os
import subprocess
import time
import json
import re
from datetime import datetime
from typing import Optional, Callable
import queue
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from src.config import REACT_SCREENSHOTS_DIR, WORKSPACE_ROOT
from src.desktop_controller import DesktopATC

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
    
    def __init__(self, atc, api_key: str = None, remote_click_queue: queue.Queue = None, enable_desktop: bool = True):
        """
        Args:
            atc: ATC (Air Traffic Controller) インスタンス - 実際の操作を行う
            api_key: Google API Key
        """
        self.atc = atc
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.max_steps = 50  # 無限ループ防止（複雑なタスク対応）
        self.collected_data = {}  # 収集したデータ（URL等）
        self.history = []  # 行動履歴
        self.screenshot_dir = str(REACT_SCREENSHOTS_DIR)
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.remote_click_queue = remote_click_queue
        
        # Desktop Integration
        self.enable_desktop = enable_desktop
        self.desktop_atc = DesktopATC() if enable_desktop else None
        self.current_mode = "web"  # "web" or "desktop"
        
        # Human-in-the-Loop用
        import threading
        self.pause_event = threading.Event()
        self.pause_event.set() # 初期状態は実行中
        self.user_response = None
        self.awaiting_user = False
        
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
                "final_result": str,
                "video_path": str | None
            }
        """
        print(f"\n{'='*50}")
        print(f"🎯 ReAct Agent Starting")
        print(f"   Goal: {goal}")
        print(f"{'='*50}\n")
        
        self.history = []
        step_count = 0
        video_path = None
        
        try:
            # ブラウザセッション開始（動画録画も開始）
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
                    video_path = self.atc.stop_session()
                    return {
                        "success": True,
                        "steps_taken": step_count,
                        "history": self.history,
                        "final_result": thought.get("result", "Task completed"),
                        "video_path": video_path
                    }
                
                if thought.get("action") == "fail":
                    print(f"\n❌ Agent determined task cannot be completed")
                    video_path = self.atc.stop_session()
                    return {
                        "success": False,
                        "steps_taken": step_count,
                        "history": self.history,
                        "final_result": thought.get("reason", "Failed to complete task"),
                        "video_path": video_path
                    }
                
                # Human-in-the-Loop: ユーザーへの質問
                if thought.get("action") == "ask_user":
                    print(f"\n✋ Awaiting human intervention: {thought.get('params', {}).get('question')}")
                    self.awaiting_user = True
                    self.pause_event.clear() # ポーズ状態にする
                    
                    # コールバックがあれば現在の状態をUIに通知（サーバー経由でUIを更新するため）
                    if on_step:
                        on_step(step_count, thought, screenshot_path)
                    
                    # ユーザーの再開を待つ（リモートクリックも処理）
                    while not self.pause_event.is_set():
                        # リモートクリックキューをチェック
                        if self.remote_click_queue:
                            try:
                                x, y = self.remote_click_queue.get_nowait()
                                if self.atc.page:
                                    self.atc.page.mouse.click(x, y)
                                    print(f"   🖱️ Executed Remote Click at ({x}, {y})")
                                    time.sleep(0.5)  # クリック後少し待機
                            except queue.Empty:
                                pass  # キューが空
                        time.sleep(0.1)  # CPU負荷軽減
                    
                    print(f"▶️ Resuming with user response: {self.user_response}")
                    self.awaiting_user = False
                    # ユーザーの回答を履歴に追加して、次の思考に役立てる
                    self.history.append({
                        "step": step_count,
                        "timestamp": datetime.now().isoformat(),
                        "role": "user_intervention",
                        "response": self.user_response
                    })
                    # アクション実行はスキップして次のループ（Observe）に戻る
                    continue

                # 4. ACT: アクションを実行
                # 4. ACT: アクションを実行
                action_result = self._act(thought)

                # 結果を履歴に保存（次のThinkで使うため）
                if self.history:
                    self.history[-1]["action_result"] = action_result
                
                # アクションに応じた待機
                if thought.get("action") in ["goto", "click", "key"]:
                    time.sleep(2)  # ページ遷移を待つ
                else:
                    time.sleep(1)
            
            # 最大ステップ数到達
            print(f"\n⚠️ Max steps ({self.max_steps}) reached")
            video_path = self.atc.stop_session()
            return {
                "success": False,
                "steps_taken": step_count,
                "history": self.history,
                "final_result": "Max steps reached without completing goal",
                "video_path": video_path
            }
            
        except Exception as e:
            print(f"\n💥 Error: {e}")
            try:
                video_path = self.atc.stop_session()
            except:
                pass
            return {
                "success": False,
                "steps_taken": step_count,
                "history": self.history,
                "final_result": f"Error: {str(e)}",
                "video_path": video_path
            }
    
    def _capture_screen(self, step: int, click_point: tuple = None) -> str:
        """現在の画面をキャプチャ。click_pointがあれば赤丸を描画"""
        path = f"{self.screenshot_dir}/step_{step}_{int(time.time())}.png"
        
        if self.current_mode == "desktop" and self.desktop_atc:
            path = self.desktop_atc.capture_screen(prefix=f"step_{step}")
        elif self.atc.page:
            self.atc.page.screenshot(path=path)
        else:
            import pyautogui
            pyautogui.screenshot(path)
            
        # クリック地点の可視化
        if click_point and all(isinstance(coord, (int, float)) for coord in click_point):
            try:
                from PIL import ImageDraw
                img = Image.open(path)
                draw = ImageDraw.Draw(img)
                x, y = click_point
                r = 10
                draw.ellipse((x-r, y-r, x+r, y+r), outline="red", width=3)
                img.save(path)
            except Exception as e:
                print(f"   ⚠️ Visualization Error: {e}")
                
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

## 重要: ユーザーの回答があれば、それに従って行動してください
履歴に「👤 ユーザーの回答:」がある場合、その内容を最優先で考慮してください。
同じ質問を繰り返さないでください。ユーザーが回答したら、その内容に基づいて次のアクション（検索、移動など）を実行してください。

## 現在のステップ
{step}/{self.max_steps}

⚠️ 効率化ガイダンス:
- ステップ35以降: より直接的なアプローチを優先してください（探索的な行動を減らす）
- ステップ45以降: 最短ルートのみを選択してください（試行錯誤を避ける）
- 常に: 同じアクションの繰り返しを避け、前のステップから学習してください


## 利用可能なアクション

1. **goto** - URLに移動
   - params: {{"url": "https://..."}}

2. **click** - 画面上の要素をクリック（座標指定）
   - params: {{"x": 100, "y": 200, "description": "何をクリックするか"}}

3. **type** - テキストを入力（現在フォーカスされている場所に）
   - params: {{"text": "入力するテキスト", "submit": true/false}}
   - **submit: true** にすると、入力後に自動的にEnterキーが押されます（検索実行に便利）
   - 例: {{"text": "イヤホン", "submit": true}} → 入力後すぐに検索実行

4. **key** - キーを押す
   - params: {{"key": "Enter" | "Tab" | "Escape" | "Backspace" など}}

5. **scroll** - スクロール
   - params: {{"direction": "up" | "down", "amount": 300}}

6. **wait** - 待機（ページ読み込みなど）
   - params: {{"seconds": 2}}

7. **read** - 画面から情報を読み取る（結果をメモする）
   - params: {{"target": "何を読み取るか", "result": "読み取った内容"}}

8. **get_url** - 現在のページのURLを取得してメモリに保存
   - params: {{"label": "product_url"}}  ← ラベル名は product_url を使ってください
   - 注意: これで取得したURLはsave_fileで {{{{url:product_url}}}} として参照できます

9. **save_file** - テキストをファイルに直接保存（Linuxコマンド不要）
   - params: {{"filename": "results/output.txt", "content": "保存する内容", "append": true/false}}
   - 注意: get_urlで取得したURLを使う場合は content に "{{{{url:product_url}}}}" と書くと自動置換されます
   - 重要: **save_file実行後は必ず done アクションでタスク完了を宣言してください**

10. **ask_user** - 人間に助けを求める（CAPTCHA、ログイン、判断に迷う場合など）
    - params: {{"question": "何をしてほしいかの具体的な説明"}}
    - 例: {{"question": "CAPTCHAが表示されました。パズルを解いてからResumeボタンを押してください。"}}
    - 例: {{"question": "複数の候補が見つかりました。どちらを選びますか？ (AかBか)"}}

11. **run_terminal** - CLIコマンドを実行（ファイル操作、印刷など）
    - params: {{"command": "wget https://example.com/file.pdf"}}
    - 例: {{"command": "lp -d EPSON_EP808AW paper.pdf"}}
    - 注意: GUIでのダウンロードや印刷が困難な場合は、このアクションを優先して使用してください

12. **done** - ゴール達成、タスク完了
    - params: {{"result": "達成した結果の説明"}}

13. **fail** - タスク完了不可能と判断
    - params: {{"reason": "なぜ完了できないか"}}

## 戦略ガイド（重要）
- **Web情報収集**: 最新情報はブラウザ(goto/click)で探してください。
- **ファイル取得**: PDFなどのファイルへのリンクを見つけたら、クリックではなく `run_terminal` + `wget/curl` でダウンロードするのが最も確実です。
- **印刷**: PDFを開いて印刷ボタンを押す（GUI）よりも、`run_terminal` + `lp` コマンドを使う方が遥かに簡単で確実です。
- したがって、「検索(Web GUI) → URL特定 → ダウンロード(CLI) → 印刷(CLI)」というハイブリッド戦略が最短ルートです。

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
    
    def _act(self, thought: dict) -> str:
        """決定されたアクションを実行し、結果メッセージを返す"""
        action = thought.get("action", "wait")
        params = thought.get("params", {})
        result_msg = f"Executed {action}"
        
        try:
            if action == "goto":
                url = params.get("url", "https://www.google.com")
                self.atc.nav(url)
                result_msg = f"Navigated to {url}"
                
            elif action == "click":
                x = params.get("x", 0)
                y = params.get("y", 0)
                click_count = params.get("click_count", 1)  # トリプルクリック対応
                if self.atc.page:
                    time.sleep(0.3)
                    self.atc.page.mouse.click(x, y, click_count=click_count)
                    time.sleep(0.5)
                    result_msg = f"Clicked at ({x}, {y}) x{click_count}"
                else:
                    import pyautogui
                    pyautogui.click(x, y, clicks=click_count)
                    result_msg = f"Clicked at ({x}, {y}) x{click_count} (Desktop)"
                
            elif action == "type":
                text = params.get("text", "")
                submit = params.get("submit", False)  # 入力後にEnterを押すオプション
                if self.atc.page:
                    # フォーカスがあたっている前提で直接入力
                    self.atc.page.keyboard.type(text, delay=30)
                    if submit:
                        time.sleep(0.2)
                        self.atc.page.keyboard.press("Enter")
                        result_msg = f"Typed and submitted: {text}"
                    else:
                        result_msg = f"Typed: {text}"
                    time.sleep(0.3)
                else:
                    import pyautogui
                    pyautogui.write(text, interval=0.03)
                    if submit:
                        pyautogui.press('enter')
                        result_msg = f"Typed and submitted: {text} (Desktop)"
                    else:
                        result_msg = f"Typed: {text} (Desktop)"
                
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
                result_msg = f"Scrolled {direction} by {amount}px"
                
            elif action == "wait":
                seconds = params.get("seconds", 2)
                time.sleep(seconds)
                result_msg = f"Waited {seconds}s"
                
            elif action == "read":
                target = params.get("target", "unknown")
                result = params.get("result", "")
                result_msg = f"Read '{target}': {result}"
                # 結果をファイルに保存
                with open("/workspaces/Airport/results/react_readings.txt", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] {target}: {result}\n")
                
            elif action == "get_url":
                label = params.get("label", "current_url")
                if self.atc.page:
                    url = self.atc.page.url
                    self.collected_data[label] = url
                    result_msg = f"Got URL [{label}]: {url}"
                else:
                    result_msg = "No page available to get URL"
                
            elif action == "save_file":
                filename = params.get("filename", "results/output.txt")
                content = params.get("content", "")
                append = params.get("append", False)
                
                # Warn if placeholders exist without collected values
                placeholder_labels = set(re.findall(r"\{\{?url:([^}]+)\}?\}", content))
                for label in placeholder_labels:
                    if label not in self.collected_data:
                        print(f"   ⚠️ No collected URL for label '{label}'")

                # URLプレースホルダーを置換
                for label, url in self.collected_data.items():
                    content = content.replace(f"{{{{url:{label}}}}}", url)
                    content = content.replace(f"{{url:{label}}}", url)  # 念のため両方対応
                
                # ファイルパスの処理
                if not os.path.isabs(filename):
                     # WORKSPACE_ROOT が未定義かもしれないので絶対パス決め打ち
                    filename = f"/workspaces/Airport/{filename}"
                
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                mode = "a" if append else "w"
                with open(filename, mode, encoding="utf-8") as f:
                    f.write(content)
                result_msg = f"Saved to {filename}"
                
            elif action == "ask_user":
                question = params.get("question", "")
                self.awaiting_user = True
                result_msg = f"Asked user: {question}"
            
            elif action == "done":
                result = params.get("result", "Goal achieved")
                result_msg = f"Done: {result}"
                return json.dumps({"success": True, "final_result": result, "message": result_msg})
                
            elif action == "fail":
                reason = params.get("reason", "Unknown error")
                result_msg = f"Failed: {reason}"
                return json.dumps({"success": False, "final_result": reason, "message": result_msg})

            elif action == "launch_app":
                command = params.get("command", "")
                if self.desktop_atc:
                    self.desktop_atc.launch_app(command)
                    self.current_mode = "desktop"
                    result_msg = f"Launched app: {command}"
            
            elif action == "click_desktop":
                if self.desktop_atc:
                    instruction = params.get("instruction", "")
                    self.desktop_atc.click_vision(instruction)
                    result_msg = f"Desktop Click: {instruction}"
            
            elif action == "type_desktop":
                if self.desktop_atc:
                    instruction = params.get("instruction", "")
                    text = params.get("text", "")
                    self.desktop_atc.type_vision(instruction, text)
                    result_msg = f"Typed on Desktop: {text}"
            
            elif action == "press_hotkey":
                if self.desktop_atc:
                    keys = params.get("keys", [])
                    if isinstance(keys, list) and keys:
                        self.desktop_atc.press_hotkey(*keys)
                        result_msg = f"Hotkey: {' + '.join(keys)}"
            
            elif action == "print_document":
                # print_document は launch_app + hotkey のショートカットなので
                # メッセージもそれを反映
                if self.desktop_atc:
                    filepath = params.get("filepath", "")
                    self.desktop_atc.launch_app(f"evince {filepath} &")
                    self.current_mode = "desktop"
                    time.sleep(3)
                    self.desktop_atc.press_hotkey("ctrl", "p")
                    time.sleep(2)
                    self.desktop_atc.click_vision("Print button")
                    result_msg = f"Printing sequence executed for {filepath}"

            elif action == "run_terminal":
                command = params.get("command", "")
                try:
                    if command.strip().endswith("&"):
                        subprocess.Popen(command, shell=True)
                        result_msg = f"Started background command: {command}"
                    else:
                        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                        output_snippet = (res.stdout + res.stderr).strip()[:500] # 長めに取得
                        if res.returncode == 0:
                            result_msg = f"Command Success: {output_snippet or '(no output)'}"
                        else:
                            result_msg = f"Command Failed (code {res.returncode}): {output_snippet}"
                except Exception as e:
                    result_msg = f"Command Error: {str(e)}"
            
            elif action == "switch_to_web":
                self.current_mode = "web"
                result_msg = "Switched to Web mode"
                
        except Exception as e:
            print(f"Error executing action {action}: {e}")
            result_msg = f"Error executing {action}: {str(e)}"

        print(f"   ▶️ {result_msg}")
        return result_msg
    
    def _format_history(self) -> str:
        """履歴をテキストにフォーマット"""
        if not self.history:
            return "(まだ行動していません)"
        
        lines = []
        for h in self.history[-7:]:  # 直近7ステップ（ユーザー介入を含むため増やす）
            if h.get("role") == "user_intervention":
                # ユーザーからの回答
                lines.append(f"👤 ユーザーの回答: 「{h.get('response', '')}」")
            else:
                thought = h.get("thought", {})
                action = thought.get('action', '?')
                if action == "ask_user":
                    lines.append(f"Step {h['step']}: ask_user - 質問: {thought.get('params', {}).get('question', '')[:80]}")
                else:
                    observation = thought.get('observation', '')[:80]
                    result = h.get('action_result', '')
                    if result:
                         lines.append(f"Step {h['step']}: {action} - Result: {result}")
                    else:
                         lines.append(f"Step {h['step']}: {action} - {observation}")
        
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
