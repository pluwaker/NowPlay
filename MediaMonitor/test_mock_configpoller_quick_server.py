
import sys
from flask import Flask, request, jsonify
from datetime import datetime
import threading
import os

app = Flask(__name__)
config_failure_mode = False
config_failure_lock = threading.Lock()

def is_config_failure_mode():
    with config_failure_lock:
        return config_failure_mode

def set_config_failure_mode(enabled):
    global config_failure_mode
    with config_failure_lock:
        config_failure_mode = enabled

@app.route('/update', methods=['POST'])
def update():
    try:
        data = request.get_json()
        timestamp = datetime.now().isoformat()
        
        # Log to file
        with open('test_configpoller_quick_server_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp}|{data.get('artist', 'Unknown')}|{data.get('title', 'Unknown')}|{data.get('position', 0)}|{data.get('isPlaying', False)}\n")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_config', methods=['GET'])
def get_config():
    timestamp = datetime.now().isoformat()
    
    # Check if we should simulate failure
    if is_config_failure_mode():
        # Log failed request
        with open('test_configpoller_quick_config_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp}|FAILED|Simulated failure\n")
        
        # Return 500 error to simulate failure
        return jsonify({"error": "Simulated config failure"}), 500
    else:
        # Log successful request
        with open('test_configpoller_quick_config_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp}|SUCCESS|\n")
        
        # Return normal config
        return jsonify({"selected_media_source": "auto"}), 200

@app.route('/sources', methods=['POST'])
def sources():
    return jsonify({"status": "ok"}), 200

@app.route('/control/config_failure', methods=['POST'])
def control_config_failure():
    data = request.get_json()
    enabled = data.get('enabled', False)
    set_config_failure_mode(enabled)
    return jsonify({"status": "ok", "config_failure_mode": enabled}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False, threaded=True)
