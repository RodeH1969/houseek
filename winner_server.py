from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import re
import traceback

app = Flask(__name__, static_folder='static')
CORS(app)

# Enhanced address variants
ADDRESS_VARIANTS = [
    "37 Yoku Road Ashgrove",
    "37 Yoku Road, Ashgrove QLD, Australia",
    "37 Yoku Rd Ashgrove",
    "37 Yoku Rd, Ashgrove",
    "37 yoku road ashgrove",
    "37 yoku rd ashgrove"
]

# Pre-normalized versions
CORRECT_ADDRESS_VARIANTS = []

def normalize_address(addr):
    addr = addr.lower().strip()
    addr = re.sub(r'[^\w\s]', '', addr)  # Remove punctuation
    addr = re.sub(r'\s+', ' ', addr)     # Collapse spaces
    return addr

# Initialize normalized variants
CORRECT_ADDRESS_VARIANTS = [normalize_address(a) for a in ADDRESS_VARIANTS]

def log_debug(info):
    os.makedirs("winners", exist_ok=True)
    with open("winners/debug_log.txt", "a") as f:
        f.write(f"{datetime.now()} - {info}\n")

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    try:
        data = request.json
        address = data.get("address", "").strip()
        log_debug(f"Submission attempt: {address}")
        
        norm_input = normalize_address(address)
        log_debug(f"Normalized input: {norm_input}")
        
        if norm_input in CORRECT_ADDRESS_VARIANTS:
            log_debug("Address matched!")
            return jsonify({"status": "correct"})
        else:
            log_debug(f"No match. Input: {norm_input} | Variants: {CORRECT_ADDRESS_VARIANTS}")
            return jsonify({"status": "incorrect"})
            
    except Exception as e:
        log_debug(f"Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error"})

@app.route("/")
def serve():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)