# デスクトップアクションの実装コード（react_agent.pyの_actメソッドに追加する部分）

            # === Desktop Actions ===
            elif action == "launch_app":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                    return
                
                command = params.get("command", "")
                print(f"   🖥️ Launching App: {command}")
                self.desktop_atc.launch_app(command)
                self.current_mode = "desktop"
                print("   ✅ Switched to Desktop mode")
            
            elif action == "click_desktop":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                    return
                
                instruction = params.get("instruction", "")
                print(f"   🖱️ Desktop Click: {instruction}")
                self.desktop_atc.click_vision(instruction)
            
            elif action == "type_desktop":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                    return
                
                instruction = params.get("instruction", "")
                text = params.get("text", "")
                print(f"   ⌨️ Desktop Type: '{text}' at '{instruction}'")
                self.desktop_atc.type_vision(instruction, text)
            
            elif action == "press_hotkey":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                    return
                
                keys = params.get("keys", [])
                if isinstance(keys, list) and len(keys) > 0:
                    print(f"   🎹 Hotkey: {' + '.join(keys)}")
                    self.desktop_atc.press_hotkey(*keys)
                else:
                    print("   ⚠️ Invalid hotkey format")
            
            elif action == "print_document":
                if not self.desktop_atc:
                    print("   ⚠️ Desktop mode is disabled")
                    return
                
                filepath = params.get("filepath", "")
                print(f"   🖨️ Printing: {filepath}")
                
                # 1. PDFビューアで開く
                self.desktop_atc.launch_app(f"evince {filepath} &")
                self.current_mode = "desktop"
                time.sleep(3)
                
                # 2. 印刷ダイアログを開く（Ctrl+P）
                self.desktop_atc.press_hotkey("ctrl", "p")
                time.sleep(2)
                
                # 3. Printボタンをクリック
                self.desktop_atc.click_vision("Click the Print button")
                print("   ✅ Print job sent")
            
            elif action == "switch_to_web":
                print("   🌐 Switching to Web mode")
                self.current_mode = "web"
