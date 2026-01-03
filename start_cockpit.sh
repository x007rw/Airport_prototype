#!/bin/bash
echo "✈️  AIRPORT COCKPIT SYSTEM STARTING..."

# 1. 物理的な強制クリーンアップ (lsofを使用)
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
DISPLAY="${DISPLAY:-:99}"

echo "🧹 Emergency cleaning of ports ${FRONTEND_PORT} and ${BACKEND_PORT}..."
LSOF_PIDS=$(lsof -ti:${FRONTEND_PORT},${BACKEND_PORT})
if [ ! -z "$LSOF_PIDS" ]; then
    echo "Found ghost processes: $LSOF_PIDS. Terminating..."
    kill -9 $LSOF_PIDS 2>/dev/null
fi
rm -rf frontend/.next/dev/lock 2>/dev/null
sleep 2

# 2. 環境変数の読み込み
echo "🔑 Loading environment variables..."
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "   GOOGLE_API_KEY is set: ${GOOGLE_API_KEY:0:10}..."
fi

# 3. バックエンド起動
echo "🔹 Launching ATC Backend (Port ${BACKEND_PORT})..."
export PYTHONPATH=$PYTHONPATH:.
# ログに出力してバックグラウンド実行
uvicorn src.server:app --host 0.0.0.0 --port ${BACKEND_PORT} > results/server_output.log 2>&1 &

# 4. バックエンドの起動待ち (ヘルスチェック)
echo "⏳ Waiting for Backend to stabilize..."
for i in {1..15}; do
    if curl -s http://localhost:${BACKEND_PORT}/api/status > /dev/null; then
        echo "✅ Backend is ONLINE."
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Backend failed to start. Check results/server_output.log"
        exit 1
    fi
    sleep 1
done

# 5. フロントエンド起動
echo "🔹 Launching Cockpit UI (Port ${FRONTEND_PORT})..."
cd frontend
# 明示的にポート3000を指定し、バックグラウンドへ
npm run dev -- -p ${FRONTEND_PORT} &

echo "--------------------------------------------------"
echo "🚀 PROJECT AIRPORT IS READY"
echo "URL: http://localhost:${FRONTEND_PORT}"
echo "--------------------------------------------------"
echo "Setup complete. The browser should now be responsive."

# プロセスを維持するための待機
wait
