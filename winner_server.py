from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import json
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

WINNERS_FILE = "winners/winners.json"
WINNERS_BACKUP_FILE = "winners/winners_backup.json"
LOG_FILE = "winners/winners.log"
ATTEMPTS_FILE = "winners/address_attempts.txt"
CURRENT_HOUSE_TXT = "static/current_house.txt"
HOUSES_DIR = "static/houses"

# Utility functions

def read_winners():
    if os.path.exists(WINNERS_FILE):
        with open(WINNERS_FILE, "r") as f:
            return json.load(f)
    return []

def write_winners(data):
    with open(WINNERS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    with open(WINNERS_BACKUP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_winner(name, mobile, guess, correct, house_number):
    now = datetime.now().isoformat()
    log_entry = f"[{now}] ✅ WINNER: {name}, {mobile}, house{house_number}: '{guess}'\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def log_attempt(guess, correct, house_number):
    now = datetime.now().isoformat()
    log_entry = f"[{now}] ❌ ATTEMPT on house{house_number}: '{guess}' vs '{correct}'\n"
    with open(ATTEMPTS_FILE, "a") as f:
        f.write(log_entry)

def normalize(s):
    return s.strip().lower().replace(",", "").replace(".", "")

def get_total_houses():
    return len([f for f in os.listdir(HOUSES_DIR) if f.startswith("house") and f.endswith(".png") and "_mobile" not in f])

# NEW: Get current house number from static/current_house.txt
def get_current_house_number():
    with open(CURRENT_HOUSE_TXT) as f:
        return int(f.read().strip())

def set_next_house_number(next_num):
    with open(CURRENT_HOUSE_TXT, "w") as f:
        f.write(str(next_num))

# Routes

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/get-winners")
def get_winners():
    return jsonify(read_winners())

@app.route("/get-current-house")
def get_current_house():
    number = get_current_house_number()
    return jsonify({"number": number})

@app.route("/submit-address", methods=["POST"])
def submit_address():
    data = request.json
    guess = data.get("guess", "")
    name = data.get("name", "")
    mobile = data.get("mobile", "")
    trigger_next = data.get("triggerNext", False)

    current_number = get_current_house_number()
    address_file = os.path.join(HOUSES_DIR, f"house{current_number}_address.txt")

    if not os.path.exists(address_file):
        return jsonify({"success": False, "error": "Address not found"}), 404

    with open(address_file, "r") as f:
        correct_address = f.read().strip()

    if normalize(guess) == normalize(correct_address):
        winners = read_winners()
        winners.append({
            "name": name,
            "mobile": mobile,
            "house": f"house{current_number}",
            "guess": guess,
            "timestamp": datetime.now().isoformat()
        })
        write_winners(winners)
        log_winner(name, mobile, guess, correct_address, current_number)

        if trigger_next:
            next_number = current_number + 1
            total = get_total_houses()
            if next_number < total:
                set_next_house_number(next_number)

        return jsonify({"success": True, "correct": True, "currentHouse": current_number})

    else:
        log_attempt(guess, correct_address, current_number)
        return jsonify({"success": True, "correct": False, "currentHouse": current_number})

# Entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
