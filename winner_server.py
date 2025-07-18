from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import re

app = Flask(__name__, static_folder='static')
CORS(app)

# Acceptable address variants
CORRECT_ADDRESS_VARIANTS = [
    "37 Yoku Rd Ashgrove",
    "37 Yoku Road, Ashgrove QLD, Australia"
]

# Normalize address: lowercase, strip punctuation, extra spaces
def normalize_address(addr):
    addr = addr.lower()
    addr = re.sub(r'[^\w\s]', '', addr)  # remove punctuation
    addr = re.sub(r'\s+', ' ', addr)  # collapse multiple spaces
    return addr.strip()

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    data = request.json
    address = data.get("address", "").strip()
    name = data.get("name", "").strip()
    mobile = data.get("mobile", "").strip()
    over18 = data.get("over18", True)

    # Log attempt
    os.makedirs("winners", exist_ok=True)
    with open("winners/address_attempts.txt", "a") as f:
        f.write(f"{datetime.now()} - {name} - {address}\n")

    norm_input = normalize_address(address)
    norm_variants = [normalize_address(a) for a in CORRECT_ADDRESS_VARIANTS]

    if norm_input not in norm_variants:
        return jsonify({"status": "incorrect"})

    if not name or not mobile or not over18:
        return jsonify({"status": "missing_info"})

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    winner_filename = f"winners/winner-{timestamp}.txt"
    with open(winner_filename, "w") as f:
        f.write(f"Winner: {name}\nMobile: {mobile}\nAddress: {address}\nTime: {timestamp}\n")
    with open("winners/winners.txt", "a") as f:
        f.write(f"{name} - {mobile} - {address} - {timestamp}\n")

    return jsonify({"status": "correct"})

@app.route("/log-guess", methods=["POST"])
def log_guess():
    data = request.json
    guess = data.get("guess", "")
    with open("winners/guesses.txt", "a") as f:
        f.write(f"{datetime.now()} - {guess}\n")
    return jsonify({"status": "logged"})

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)