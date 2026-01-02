# ✈️ Airport: 次世代型 AI GUI エージェント・プラットフォーム

**Airport** は、Webブラウザとデスクトップアプリケーションをシームレスに操作する、高度な自律型GUIエージェント・フレームワークです。

**Google Gemini 2.0 Flash** の視覚能力（Vision）を核としており、人間と同じように画面を「見て」理解し、ボタンのクリック、情報の読み取り、複雑なタスクの完遂を自律的に行います。

---

## 🌟 主な特徴

*   **ハイブリッドWebオートメーション**: DOMセレクタの正確さと、AIによる視覚的理解（Vision）を統合。UIの変更にも柔軟に対応します。
*   **Vision-Only デスクトップ制御**: OSネイティブアプリ（電卓、メモ帳、独自ツール等）を、視覚情報のみで操作可能。
*   **統合コックピット (GUI)**: Next.js製の洗練されたダッシュボードから、ミッションの発令、実行ログの監視、録画の再生が可能です。
*   **自律的推論と修復**: タスクが失敗しても、AIが原因を分析し、自力で代替ルートを探して目的を果たします。
*   **フライトレコーダー**: 実行中の全ての操作を動画として記録。後からの監査やプレゼンに活用できます。

---

## 📂 プロジェクト構成

```text
/workspaces/Airport/
├── start_cockpit.sh    # 【重要】システム一括起動スクリプト
├── run_airport.py      # CLIエントリーポイント
├── src/                # バックエンド・エンジン（FastAPI, Playwright, Gemini）
├── frontend/           # コックピットUI（Next.js + Tailwind CSS）
├── scenarios/          # ワークフロー定義ファイル (YAML)
├── scripts/            # 統合デモ・スクリプト
├── results/            # 実行結果（ログ、スクリーンショット、動画）
└── docs/               # 調査報告書・技術資料
```

---

## 🚀 クイックスタート

プロトタイプのコックピットを立ち上げるには、以下のコマンドを実行します。

```bash
chmod +x start_cockpit.sh
./start_cockpit.sh
```

### 🌍 アクセス先
*   **メイン・コックピット**: `http://localhost:3000`
*   **API ドキュメント**: `http://localhost:8000/docs`

---

## 🧠 アーキテクチャ

### Vision Core (`src/llm_core.py`)
Gemini 2.0 Flash を使用して画面を解析します。
*   ボタンや入力エリアの**座標特定**
*   画面上の文字情報（電話番号、天気等）の**テキスト抽出**

### ATC Backend (`src/server.py`)
Python (FastAPI) で構築された管制システムです。フロントエンドからの指令を受け取り、Captain（エージェント）にミッションを割り当てます。

### Cockpit UI (`frontend/`)
Next.js によるモダンなダッシュボードです。プロセスのリアルタイム監視と、フライト情報の可視化を担います。

---
*Created by Project Airport Team - Empowering AI to act.*
