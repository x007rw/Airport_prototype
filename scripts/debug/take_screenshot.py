import pyautogui
import time
import os

# Xvfb環境のディスプレイを指定
# os.environ["DISPLAY"] = ":99" 
# ↑ 既に環境変数で設定されているはずですが、displayは main.py の ensure_display で確認済み

time.sleep(1)
screenshot = pyautogui.screenshot()
screenshot.save("/workspaces/Airport/desktop_capture.png")
print("Desktop captured.")
