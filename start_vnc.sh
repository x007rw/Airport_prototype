#!/bin/bash
# VNC/noVNC サーバー起動スクリプト
# ブラウザから http://localhost:6080 へアクセスしてリアルタイム操作

echo "🖥️  Starting VNC Server for Airport..."

# 既存のプロセスを停止
pkill -f "Xvfb :99" 2>/dev/null
pkill -f "x11vnc" 2>/dev/null
pkill -f "websockify.*6080" 2>/dev/null

# 仮想ディスプレイを起動 (1280x720)
export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &
sleep 2

echo "✅ Virtual display :99 started (1280x720)"

# x11vnc サーバーを起動 (パスワードなし、ポート5900)
x11vnc -display :99 -forever -nopw -rfbport 5900 -shared -bg -o /tmp/x11vnc.log
sleep 1

echo "✅ x11vnc server started on port 5900"

# noVNC (websockify) を起動 - ブラウザからアクセス可能に
websockify --web=/usr/share/novnc 6080 localhost:5900 &
sleep 1

echo "✅ noVNC started on port 6080"
echo ""
echo "=================================================="
echo "🌐 Access VNC via browser:"
echo "   http://localhost:6080/vnc.html"
echo "=================================================="
echo ""
echo "Now you can start the Airport server with DISPLAY=:99"
echo "Example: DISPLAY=:99 ./start_cockpit.sh"
