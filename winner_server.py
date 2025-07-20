from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re
import json

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
HOUSES_DIR = Path("static/houses")
CURRENT_HOUSE_FILE = Path("static/current_house.txt")
WINNERS_FILE = Path("winners/winners.json")

def init_files():
    os.makedirs("winners", exist_ok=True)
    if not CURRENT_HOUSE_FILE.exists():
        CURRENT_HOUSE_FILE.write_text("1")  # Start with house1
    if not WINNERS_FILE.exists():
        with open(WINNERS_FILE, 'w') as f:
            json.dump([], f)

def get_max_house_number():
    """Dynamically finds the highest house number available"""
    max_num = 0
    for file in os.listdir(HOUSES_DIR):
        if file.startswith('house') and file.endswith('.png'):
            try:
                num = int(file[5:-4])  # Extract number from 'houseX.png'
                max_num = max(max_num, num)
            except ValueError:
                continue
    return max_num if max_num > 0 else 1  # Default to 1 if no houses found

def get_current_house():
    return int(CURRENT_HOUSE_FILE.read_text())

def get_required_address():
    house_num = get_current_house()
    address_file = HOUSES_DIR / f"house{house_num}_address.txt"
    if not address_file.exists():
        return f"Address not found for house {house_num}"
    return address_file.read_text().strip()

def normalize_address(address):
    return re.sub(r'[,\s]+', ' ', address.strip()).lower()

def rotate_house():
    """Rotates to next house, automatically wrapping when needed"""
    current_num = get_current_house()
    max_num = get_max_house_number()
    next_num = current_num + 1 if current_num < max_num else 1
    CURRENT_HOUSE_FILE.write_text(str(next_num))
    return next_num

def load_winners():
    try:
        with open(WINNERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_winners(winners):
    with open(WINNERS_FILE, 'w') as f:
        json.dump(winners, f, indent=2)

init_files()

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    data = request.json
    
    if 'address' in data:
        user_address = normalize_address(data['address'])
        required_address = normalize_address(get_required_address())
        if user_address == required_address:
            return jsonify({
                "status": "correct",
                "current_house": get_current_house(),
                "current_address": get_required_address()
            })
        return jsonify({"status": "incorrect"})
    
    elif 'name' in data and 'mobile' in data:
        winners = load_winners()
        current_house_num = get_current_house()
        current_address = get_required_address()
        
        new_house_num = rotate_house()
        
        winners.append({
            "name": data.get("name", "").strip(),
            "mobile": data.get("mobile", "").strip(),
            "address": current_address,
            "houseNumber": current_house_num,
            "date": datetime.now().isoformat(),
            "prize": "$10 Woolworths Gift Card"
        })
        
        save_winners(winners)
        
        return jsonify({
            "status": "success",
            "next_house": new_house_num,
            "winnerData": {
                "name": data.get("name", "").strip(),
                "address": current_address,
                "houseNumber": current_house_num
            }
        })

@app.route("/get-current-house")
def current_house():
    return jsonify({
        "number": get_current_house(),
        "total": get_max_house_number(),  # Now shows actual total
        "address": get_required_address()
    })

@app.route("/get-winners")
def get_winners():
    return jsonify(load_winners())

@app.route('/')
def serve():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    print(f"Server started with {get_max_house_number()} houses detected")
    app.run(host='0.0.0.0', port=5001, debug=True)