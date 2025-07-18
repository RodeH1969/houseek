from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

CORRECT_ADDRESS_VARIANTS = [
    "37 Yoku Road Ashgrove", "37 Yoku Road, Ashgrove", "37 Yoku Rd Ashgrove", "37 Yoku Rd, Ashgrove",
    "37 Yoku Road Ashgrove QLD", "37 Yoku Road, Ashgrove QLD", "37 Yoku Rd, Ashgrove QLD", "37 Yoku Rd Ashgrove QLD",
    "37 Yoku Road Ashgrove QLD Australia", "37 Yoku Road, Ashgrove QLD, Australia",
    "37 Yoku Rd, Ashgrove QLD, Australia", "37 Yoku Rd Ashgrove QLD Australia"
]

def normalize_address(addr):
    return addr.lower().replace(",", "").replace("road", "rd").strip()

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    data = request.json
    address = data.get("address", "").strip()
    name = data.get("name", "").strip()
    over18 = data.get("over18", False)

    os.makedirs("winners", exist_ok=True)
    with open("winners/address_attempts.txt", "a") as f:
        f.write(f"{datetime.now()} - {name} - {address}\n")

    if not name or not over18:
        norm_input = normalize_address(address)
        norm_variants = [normalize_address(a) for a in CORRECT_ADDRESS_VARIANTS]
        if norm_input in norm_variants:
            return jsonify({"status": "missing_info"})
        return jsonify({"status": "incorrect"})

    norm_input = normalize_address(address)
    norm_variants = [normalize_address(a) for a in CORRECT_ADDRESS_VARIANTS]

    if norm_input not in norm_variants:
        return jsonify({"status": "incorrect"})

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    winner_filename = f"winners/winner-{timestamp}.txt"
    with open(winner_filename, "w") as f:
        f.write(f"Winner: {name}\nAddress: {address}\nTime: {timestamp}\n")
    with open("winners/winners.txt", "a") as f:
        f.write(f"{name} - {address} - {timestamp}\n")

    return jsonify({"status": "correct"})

@app.route("/log-guess", methods=["POST"])
def log_guess():
    data = request.json
    guess = data.get("guess", "").strip()

    os.makedirs("winners", exist_ok=True)
    with open("winners/guesses.txt", "a") as f:
        f.write(f"{datetime.now()} - {guess}\n")

    return jsonify({"status": "logged"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
