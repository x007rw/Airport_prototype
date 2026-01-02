import os
import json
import time
from datetime import datetime

class HistoryManager:
    def __init__(self, base_dir="/workspaces/Airport/results/flights"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def start_flight(self):
        """新しいフライトID（タイムスタンプベース）を生成し、ディレクトリを作成"""
        flight_id = datetime.now().strftime("flight_%Y%m%d_%H%M%S")
        flight_dir = os.path.join(self.base_dir, flight_id)
        os.makedirs(flight_dir, exist_ok=True)
        
        # 初期メタデータ
        metadata = {
            "flight_id": flight_id,
            "start_time": datetime.now().isoformat(),
            "status": "IN_PROGRESS",
            "mission": "Unknown"
        }
        self._save_json(flight_id, "metadata.json", metadata)
        return flight_id

    def log_event(self, flight_id, event_type, details):
        """Black Boxにイベントを追記 (JSONL形式)"""
        if not flight_id:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,  # VISION, THOUGHT, ACTION, SYSTEM
            "details": details
        }
        
        file_path = os.path.join(self.base_dir, flight_id, "blackbox.jsonl")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def end_flight(self, flight_id, status="COMPLETED"):
        """フライト終了処理"""
        if not flight_id:
            return
            
        metadata = self._load_json(flight_id, "metadata.json")
        if metadata:
            metadata["end_time"] = datetime.now().isoformat()
            metadata["status"] = status
            self._save_json(flight_id, "metadata.json", metadata)

    def get_all_flights(self):
        """全フライトのリストを取得"""
        flights = []
        if not os.path.exists(self.base_dir):
            return []
            
        for d in sorted(os.listdir(self.base_dir), reverse=True):
            path = os.path.join(self.base_dir, d)
            if os.path.isdir(path):
                meta = self._load_json(d, "metadata.json")
                if meta:
                    flights.append(meta)
        return flights

    def get_flight_data(self, flight_id):
        """特定のフライトのブラックボックスデータ（ログ）を取得"""
        logs = []
        file_path = os.path.join(self.base_dir, flight_id, "blackbox.jsonl")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except:
                        pass
        return logs

    def _save_json(self, flight_id, filename, data):
        path = os.path.join(self.base_dir, flight_id, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_json(self, flight_id, filename):
        path = os.path.join(self.base_dir, flight_id, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
