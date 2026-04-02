
import sys
from flask import Flask, request, jsonify
from datetime import datetime
import threading

app = Flask(__name__)
update_count = 0
lock = threading.Lock()

@app.route('/update', methods=['POST'])
def update():
    global update_count
    try:
        data = request.get_json()
        timestamp = datetime.now().isoformat()
        
        with lock:
            update_count += 1
            seq = update_count
        
        # Log to file
        with open('test_stress_quick_server_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{seq}|{timestamp}|{data.get('artist', 'Unknown')}|{data.get('title', 'Unknown')}|{data.get('position', 0)}|{data.get('isPlaying', False)}\n")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET'])
def config():
    return jsonify({"selectedSource": ""}), 200

@app.route('/sources', methods=['POST'])
def sources():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False, threaded=True)
