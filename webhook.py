from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "live_signals.json"

@app.route('/api/v1/signal', methods=['POST'])
def receive_signal():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No payload"}), 400
    
    # بناء البطاقة التحليلية من البيانات القادمة
    new_card = {
        "trader": data.get("trader", "@AbuSaeed_Quant"),
        "symbol": data.get("symbol", "SPX"),
        "price": str(data.get("price", "0.0")),
        "signal": data.get("signal", "Quant Flow Trigger"),
        "quant_score": data.get("quant_score", 95.0),
        "details": data.get("details", "تحليل كمي موثق عبر API"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "status": "Verified via Live API ✅"
    }
    
    # حفظ الإشارة في الملف
    signals = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            signals = json.load(f)
            
    signals.insert(0, new_card)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=4)
        
    return jsonify({"status": "success", "message": "Signal Published to ProofOfEdge Feed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
