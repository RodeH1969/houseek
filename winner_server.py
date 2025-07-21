from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import datetime

app = Flask(__name__)
CORS(app)

DATA_DIR = '/data' if os.environ.get('RENDER') else 'data'
STATIC_DIR = os.path.join(os.getcwd(), 'static')
WINNERS_FILE = os.path.join(DATA_DIR, 'winners.json')
CURRENT_HOUSE_FILE = os.path.join(DATA_DIR, 'current_house.json')

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/get-current-house')
def get_current_house():
    current = load_json(CURRENT_HOUSE_FILE)
    return jsonify(current)

@app.route('/get-winners')
def get_winners():
    winners = load_json(WINNERS_FILE)
    return jsonify(winners)

@app.route('/submit-winner', methods=['POST'])
def submit_winner():
    data = request.get_json()

    # Address submission (step 1)
    if 'address' in data:
        address = data['address'].strip().lower()
        current = load_json(CURRENT_HOUSE_FILE)
        correct = current.get('address', '').strip().lower()

        # Flexible matching: ignore commas and extra whitespace
        address_clean = address.replace(',', '').lower()
        correct_clean = correct.replace(',', '').lower()

        if address == correct or address_clean == correct_clean:
            return jsonify({"status": "correct"})
        else:
            return jsonify({"status": "incorrect"})

    # Winner detail submission (step 2)
    name = data.get('name', '').strip()
    mobile = data.get('mobile', '').strip()
    over18 = data.get('over18', False)

    if not name or not mobile or not over18:
        return jsonify({"status": "error", "error": "Missing fields"}), 400

    current = load_json(CURRENT_HOUSE_FILE)
    winners = load_json(WINNERS_FILE)

    new_entry = {
        "name": name,
        "mobile": mobile,
        "address": current.get("address", ""),
        "houseNumber": current.get("number", -1),
        "date": datetime.datetime.now().isoformat()
    }

    winners.append(new_entry)
    save_json(WINNERS_FILE, winners)

    # ✅ Advance to next house if requested
    if data.get("triggerNext"):
        current["number"] += 1
        current["address"] = ""  # Clear for next round — must be set manually/admin
        save_json(CURRENT_HOUSE_FILE, current)

    return jsonify({"status": "success", "winnerData": new_entry})

@app.route('/debug-status')
def debug_status():
    status = {
        "render_env": str(bool(os.environ.get('RENDER'))).lower(),
        "persistent_dir": DATA_DIR,
        "static_dir": STATIC_DIR,
        "winners_file": WINNERS_FILE,
        "winners_exists": os.path.exists(WINNERS_FILE),
        "house_file": CURRENT_HOUSE_FILE,
        "house_exists": os.path.exists(CURRENT_HOUSE_FILE),
        "house_images": [f for f in os.listdir(os.path.join(STATIC_DIR, "houses")) if f.endswith(".png")] if os.path.exists(os.path.join(STATIC_DIR, "houses")) else []
    }
    return jsonify(status)

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    if not os.path.exists(WINNERS_FILE):
        save_json(WINNERS_FILE, [])
    if not os.path.exists(CURRENT_HOUSE_FILE):
        save_json(CURRENT_HOUSE_FILE, {"number": 0, "address": ""})
    app.run(host='0.0.0.0', port=5000)
