#!/bin/bash
# Airport フルスタック起動スクリプト
# VNC + Backend + Frontend を一括起動

echo "✈️  AIRPORT FULL SYSTEM STARTING..."
echo ""

# 1. VNCサーバー起動
echo "🖥️  Step 1: Starting VNC Server..."
pkill -f "Xvfb :99" 2>/dev/null
pkill -f "x11vnc" 2>/dev/null
pkill -f "websockify.*6080" 2>/dev/null

export DISPLAY=:99
Xvfb :99 -screen 0 1280x720x24 &
sleep 2
x11vnc -display :99 -forever -nopw -rfbport 5900 -shared -bg -o /tmp/x11vnc.log
sleep 1
websockify --web=/usr/share/novnc 6080 localhost:5900 &
sleep 1
echo "   ✅ VNC ready at http://localhost:6080/vnc.html"

# 2. Cockpit起動 (Backend + Frontend)
echo ""
echo "🚀 Step 2: Starting Airport Cockpit..."
./start_cockpit.sh &

# 完了メッセージ
sleep 5
echo ""
echo "=================================================="
echo "✈️  AIRPORT IS FULLY OPERATIONAL"
echo ""
echo "📍 Cockpit UI:  http://localhost:3000"
echo "🖥️  VNC Viewer: http://localhost:6080/vnc.html"
echo "=================================================="
echo ""
echo "Usage:"
echo "  1. Open Cockpit UI to give instructions to AI"
echo "  2. Open VNC Viewer to watch/control AI's browser"
echo ""
