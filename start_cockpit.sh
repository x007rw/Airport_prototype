#!/bin/bash
echo "✈️  AIRPORT COCKPIT SYSTEM STARTING..."

# 1. 物理的な強制クリーンアップ (lsofを使用)
echo "🧹 Emergency cleaning of ports 3000 and 8000..."
LSOF_PIDS=$(lsof -ti:3000,8000)
if [ ! -z "$LSOF_PIDS" ]; then
    echo "Found ghost processes: $LSOF_PIDS. Terminating..."
    kill -9 $LSOF_PIDS 2>/dev/null
fi
rm -rf frontend/.next/dev/lock 2>/dev/null
sleep 2

# 2. バックエンド起動
echo "🔹 Launching ATC Backend (Port 8000)..."
export PYTHONPATH=$PYTHONPATH:.
# ログに出力してバックグラウンド実行
uvicorn src.server:app --host 0.0.0.0 --port 8000 > results/server_output.log 2>&1 &

# 3. バックエンドの起動待ち (ヘルスチェック)
echo "⏳ Waiting for Backend to stabilize..."
for i in {1..15}; do
    if curl -s http://localhost:8000/api/status > /dev/null; then
        echo "✅ Backend is ONLINE."
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Backend failed to start. Check results/server_output.log"
        exit 1
    fi
    sleep 1
done

# 4. フロントエンド起動
echo "🔹 Launching Cockpit UI (Port 3000)..."
cd frontend
# 明示的にポート3000を指定し、バックグラウンドへ
npm run dev -- -p 3000 &

echo "--------------------------------------------------"
echo "🚀 PROJECT AIRPORT IS READY"
echo "URL: http://localhost:3000"
echo "--------------------------------------------------"
echo "Setup complete. The browser should now be responsive."

# プロセスを維持するための待機
wait
