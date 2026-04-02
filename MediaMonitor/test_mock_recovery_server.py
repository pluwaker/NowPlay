
import sys
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        timestamp = datetime.now().isoformat()
        
        # Log to file
        with open('test_recovery_server_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp}|{data.get('artist', 'Unknown')}|{data.get('title', 'Unknown')}|{data.get('position', 0)}|{data.get('isPlaying', False)}\n")
        
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
    app.run(host='127.0.0.1', port=8080, debug=False)
