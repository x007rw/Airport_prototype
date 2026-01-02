# ✈️ Project Airport

**AI-Powered Autonomous GUI Automation Agent**

人間のように「見て、考えて、操作する」ことができる自律型AIエージェント。
Web・デスクトップ・外部システムの境界を超え、あらゆるGUI操作を自然言語で指示できます。

---

## 🌟 特徴

### 1. 視覚ベースの操作 (Vision-First)
HTML/DOMに依存せず、**画面の見た目**からAIが判断して操作します。
- Gemini 3 Flash 搭載による高精度な視覚認識
- クリック位置の自動検出
- 画面上のテキスト抽出

### 2. ReAct自律モード 🧠
**Observe → Think → Act** のループで、AIがリアルタイムで判断・行動します。
- 事前のプラン不要、動的にゴールに向かって行動
- 予期しない状況にも対応可能
- 最大25ステップまで自動実行

### 3. クロスプラットフォーム制御
ブラウザだけでなく、ネイティブデスクトップアプリも操作可能。
- Playwright によるステルスブラウザ制御
- PyAutoGUI によるOS直接制御
- ホットキー操作 (Ctrl+S, Alt+Tab など)

### 4. Mission Control (Cockpit GUI)
直感的なWebダッシュボードから、自然言語でミッションを発令。
- **Attendant**: AIアシスタントとの自然な対話
- **通常モード**: プラン確認後に実行
- **自律モード**: AIが動的に判断・行動
- **ReAct Monitor**: 各ステップの観察・推論・アクションをリアルタイム表示
- **Flight Recorder**: 全ミッションのBlack Box記録 + 動画

### 5. Black Box (フライトレコーダー)
エージェントの全ての思考・行動・結果を記録。
- 時系列ログ (JSONL形式)
- 連続動画録画（WebM形式）
- ミッション成否の追跡

---

## 📁 プロジェクト構造

```
Airport/
├── frontend/           # Next.js コックピットUI
├── src/                # コアエンジン
│   ├── main.py         # ATC (Air Traffic Controller)
│   ├── llm_core.py     # Gemini Vision + Attendant
│   ├── react_agent.py  # ReAct自律エージェント
│   ├── autopilot.py    # YAMLプラン実行
│   ├── desktop_controller.py  # デスクトップ操作
│   ├── history_manager.py     # Black Box記録
│   └── server.py       # FastAPI バックエンド
├── scenarios/          # YAMLワークフロー定義
├── results/            # ミッション成果物 (.gitignore)
│   ├── flights/        # Black Boxデータ
│   ├── videos/         # 操作録画
│   └── react_screenshots/  # ReActステップ画像
├── .env                # 環境変数（GOOGLE_API_KEY）
└── start_cockpit.sh    # 起動スクリプト
```

---

## 🚀 クイックスタート

### 1. 環境変数の設定
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
playwright install chromium
cd frontend && npm install && cd ..
```

### 3. サーバー起動
```bash
./start_cockpit.sh
```

これにより以下が起動します：
- **Backend**: http://localhost:8000 (FastAPI)
- **Frontend**: http://localhost:3000 (Next.js)

ブラウザで `http://localhost:3000` にアクセス。

---

## 🎮 使い方

### 通常モード（事前プラン確認）
1. **Attendant** に自然言語で指示（例：「東京の天気を調べて」）
2. 右側の **Mission Plan** タブでプランを確認
3. **CONFIRM & TAKE-OFF** ボタンでミッション開始
4. 完了後、**Flight Recorder** で詳細ログを確認

### 自律モード（ReActエージェント）🧠
1. 「**自律モードで**〇〇して」と指示（例：「自律モードでAmazonでイヤホンを探してURLを保存して」）
2. **ReAct Monitor** タブでリアルタイム進行を確認
   - 👁️ Observation: AIが見たもの
   - 💡 Reasoning: AIの推論
   - ⚡ Action: 実行したアクション
3. 完了後、`results/videos/` に連続動画が保存

---

## 🔧 APIエンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/status` | GET | サーバー状態 |
| `/api/chat` | POST | Attendantと会話 |
| `/api/plan` | POST | フライトプラン生成 |
| `/api/execute` | POST | プラン実行 |
| `/api/react` | POST | ReAct自律モード開始 |
| `/api/react/status` | GET | ReAct進行状況 |
| `/api/flights` | GET | フライト履歴一覧 |
| `/api/flights/{id}` | GET | フライト詳細 |

---

## 🤖 利用可能なアクション

| アクション | 説明 | 例 |
|-----------|------|-----|
| `goto` | URLに移動 | `https://amazon.co.jp` |
| `click` | 座標をクリック | `(x: 100, y: 200)` |
| `type` | テキスト入力 | `ワイヤレスイヤホン` |
| `key` | キー押下 | `Enter`, `Tab`, `Escape` |
| `scroll` | スクロール | `up`, `down` |
| `wait` | 待機 | `2秒` |
| `read` | 画面読み取り | テキスト抽出 |
| `get_url` | 現在URLを取得 | メモリに保存 |
| `save_file` | ファイル保存 | テキスト直接書き込み |
| `launch_app` | アプリ起動 | `firefox`, `mousepad` |

---

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| AI/Vision | Gemini 3 Flash Preview |
| Web自動化 | Playwright |
| Desktop自動化 | PyAutoGUI |
| Backend | FastAPI |
| Frontend | Next.js 15, React 19 |
| Recording | Playwright Video |

---

## 📹 動画録画

ReActモードでは、ミッション全体が自動録画されます：
- **形式**: WebM
- **解像度**: 1280x720
- **保存場所**: `results/videos/`

---

## 🧹 クリーンアップ

一時ファイルを削除するには：
```bash
rm -rf results/flights/*
rm -rf results/videos/*
rm -rf results/react_screenshots/*
rm -rf frontend/.next
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## 📜 ライセンス

MIT License

---

## 🔮 ロードマップ

- [x] チャットベースのAIプランニング
- [x] ReAct自律モード
- [x] 連続動画録画
- [x] ファイル保存アクション
- [ ] ライブ画面ストリーミング
- [ ] マルチタブ操作
- [ ] Windows/Mac 対応
- [ ] Multi-Agent 協調

---

**Built with 💙 by the Airport Team**
