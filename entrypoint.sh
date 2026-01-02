#!/bin/bash
# Xvfbをバックグラウンドで起動
Xvfb :99 -ac -screen 0 1280x720x24 &

# Fluxbox (ウィンドウマネージャ) を起動 (GUI操作に必要)
fluxbox &

# VNCサーバを起動 (デバッグ用)
x11vnc -display :99 -forever -nopw -listen localhost -xkb &

# コンテナが終了しないよう待機
tail -f /dev/null