#!/usr/bin/env python3
"""
Desktop Actions Integration for ReActAgent
このスクリプトは react_agent.py にデスクトップ操作機能を追加します
"""

import re

def integrate_desktop_actions():
    with open('/workspaces/Airport/src/react_agent.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. _capture_screen の更新（Desktop モード対応）
    old_capture = '''    def _capture_screen(self, step: int, click_point: tuple = None) -> str:
        """現在の画面をキャプチャ。click_pointがあれば赤丸を描画"""
        path = f"{self.screenshot_dir}/step_{step}_{int(time.time())}.png"
        
        if self.atc.page:
            self.atc.page.screenshot(path=path)
        else:
            import pyautogui
            pyautogui.screenshot(path)'''
    
    new_capture = '''    def _capture_screen(self, step: int, click_point: tuple = None) -> str:
        """現在の画面をキャプチャ。click_pointがあれば赤丸を描画"""
        path = f"{self.screenshot_dir}/step_{step}_{int(time.time())}.png"
        
        if self.current_mode == "desktop" and self.desktop_atc:
            path = self.desktop_atc.capture_screen(prefix=f"step_{step}")
        elif self.atc.page:
            self.atc.page.screenshot(path=path)
        else:
            import pyautogui
            pyautogui.screenshot(path)'''
    
    content = content.replace(old_capture, new_capture)
    
    # 2. デスクトップアクションを _act メソッドに追加
    # ask_user の後に挿入
    marker = '''            elif action == "ask_user":
                # アクションの実行自体は run メソッド内で Event を使って制御する
                pass
                
        except Exception as e:'''
    
    desktop_actions = '''            elif action == "ask_user":
                # アクションの実行自体は run メソッド内で Event を使って制御する
                pass
            
            # === Desktop Actions ===
            elif action == "launch_app":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                else:
                    command = params.get("command", "")
                    print(f"   🖥️ Launching: {command}")
                    self.desktop_atc.launch_app(command)
                    self.current_mode = "desktop"
            
            elif action == "click_desktop":
                if self.desktop_atc:
                    instruction = params.get("instruction", "")
                    print(f"   🖱️ Desktop Click: {instruction}")
                    self.desktop_atc.click_vision(instruction)
            
            elif action == "type_desktop":
                if self.desktop_atc:
                    instruction = params.get("instruction", "")
                    text = params.get("text", "")
                    self.desktop_atc.type_vision(instruction, text)
            
            elif action == "press_hotkey":
                if self.desktop_atc:
                    keys = params.get("keys", [])
                    if isinstance(keys, list) and keys:
                        print(f"   🎹 Hotkey: {' + '.join(keys)}")
                        self.desktop_atc.press_hotkey(*keys)
            
            elif action == "print_document":
                if self.desktop_atc:
                    filepath = params.get("filepath", "")
                    print(f"   🖨️ Printing: {filepath}")
                    self.desktop_atc.launch_app(f"evince {filepath} &")
                    self.current_mode = "desktop"
                    time.sleep(3)
                    self.desktop_atc.press_hotkey("ctrl", "p")
                    time.sleep(2)
                    self.desktop_atc.click_vision("Print button")
            
            elif action == "switch_to_web":
                print("   🌐 Switching to Web mode")
                self.current_mode = "web"
                
        except Exception as e:'''
    
    if marker in content:
        content = content.replace(marker, desktop_actions)
        print("✅ Desktop actions integrated")
    else:
        print("⚠️ Marker not found, skipping action integration")
    
    # 保存
    with open('/workspaces/Airport/src/react_agent.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Integration complete")

if __name__ == "__main__":
    integrate_desktop_actions()
