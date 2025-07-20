from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re
import json

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration - UPDATED WITH CORRECT PATHS
BASE_DIR = Path(r"C:\Users\apt20\OneDrive\Desktop\houseek")
HOUSES_DIR = BASE_DIR / "static" / "houses"
CURRENT_HOUSE_FILE = BASE_DIR / "static" / "current_house.txt"  # Updated path
WINNERS_FILE = BASE_DIR / "winners" / "winners.json"

def init_files():
    os.makedirs(BASE_DIR / "winners", exist_ok=True)
    if not CURRENT_HOUSE_FILE.exists():
        CURRENT_HOUSE_FILE.write_text("1")  # Start with house1
    if not WINNERS_FILE.exists():
        with open(WINNERS_FILE, 'w') as f:
            json.dump([], f)

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
    current_num = get_current_house()
    next_num = current_num + 1 if current_num < 10 else 1
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

def validate_house_addresses():
    """Check all house addresses exist and are correct"""
    print("\nValidating house addresses:")
    for i in range(1, 11):
        address_file = HOUSES_DIR / f"house{i}_address.txt"
        if not address_file.exists():
            print(f"❌ Missing: house{i}_address.txt")
            continue
            
        with open(address_file, 'r') as f:
            address = f.read().strip()
            if address:
                print(f"✅ House {i}: {address}")
            else:
                print(f"❌ Empty: house{i}_address.txt")

init_files()
validate_house_addresses()

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
        solved_house_num = get_current_house()
        solved_address = get_required_address()
        
        new_house_num = rotate_house()
        
        winner_entry = {
            "name": data.get("name", "").strip(),
            "mobile": data.get("mobile", "").strip(),
            "address": solved_address,
            "houseNumber": solved_house_num,
            "date": datetime.now().isoformat(),
            "prize": "$10 Woolworths Gift Card"
        }
        
        winners.append(winner_entry)
        save_winners(winners)
        
        return jsonify({
            "status": "success",
            "next_house": new_house_num,
            "winnerData": winner_entry
        })

@app.route("/get-current-house")
def current_house():
    return jsonify({
        "number": get_current_house(),
        "total": 10,
        "address": get_required_address()
    })

@app.route("/get-winners")
def get_winners():
    return jsonify(load_winners())

@app.route('/')
def serve():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    print(f"\nCurrent house: {get_current_house()} - {get_required_address()}")
    print(f"Winners file: {WINNERS_FILE}")
    app.run(host='0.0.0.0', port=5001, debug=True)