from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
HOUSES_DIR = Path("static/houses")
CURRENT_HOUSE_FILE = Path("static/current_house.txt")

# Initialize current house tracker
if not CURRENT_HOUSE_FILE.exists():
    CURRENT_HOUSE_FILE.write_text("1")

def get_current_house():
    """Returns the active house number (e.g. 1 for house1.png)"""
    return int(CURRENT_HOUSE_FILE.read_text())

def get_required_address():
    """Loads address from houseX_address.txt"""
    house_num = get_current_house()
    address_file = HOUSES_DIR / f"house{house_num}_address.txt"
    return address_file.read_text().strip()

def normalize_address(address):
    """Remove commas and extra spaces for comparison"""
    return re.sub(r'[,\s]+', ' ', address.strip()).lower()

def rotate_house():
    """Cycles to the next house (loops back to 1 after last)"""
    current_num = get_current_house()
    houses = sorted([f.stem for f in HOUSES_DIR.glob("house*.png")])
    next_num = current_num + 1 if current_num < len(houses) else 1
    CURRENT_HOUSE_FILE.write_text(str(next_num))
    return next_num

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    data = request.json
    print(f"Received data: {data}")  # Debug log to console
    
    # Address validation
    if 'address' in data:
        user_address = normalize_address(data['address'])
        required_address = normalize_address(get_required_address())
        if user_address == required_address:
            return jsonify({"status": "correct"})
        return jsonify({"status": "incorrect"})
    
    # Winner details submission
    elif 'name' in data:
        name = data.get("name", "").strip()
        mobile = data.get("mobile", "").strip()
        over18 = data.get("over18", False)  # Default to False if missing
        
        if not name or not mobile or not over18:
            missing = []
            if not name: missing.append("name")
            if not mobile: missing.append("mobile")
            if not over18: missing.append("age confirmation")
            print(f"Validation failed: Missing {', '.join(missing)}")  # Debug log
            return jsonify({"status": "missing_info", "error": f"Missing: {', '.join(missing)}"})
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("winners", exist_ok=True)
        with open(f"winners/winner_{timestamp}.txt", "w") as f:
            f.write(f"Name: {name}\nMobile: {mobile}\nAddress: {get_required_address()}\n")
        
        # Rotate house after successful submission
        new_house = rotate_house()
        return jsonify({
            "status": "success",
            "next_house": new_house,
            "winnerData": {
                "name": name,
                "address": get_required_address(),
                "houseNumber": new_house - 1  # The house just won
            }
        })

@app.route("/get-current-house")
def current_house():
    """Frontend uses this to load the correct house image"""
    return jsonify({
        "number": get_current_house(),
        "total": len(list(HOUSES_DIR.glob("house*.png")))
    })

@app.route('/')
def serve():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)