import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import re
import json

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration - Platform independent paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
HOUSES_DIR = BASE_DIR / "static" / "houses"
CURRENT_HOUSE_FILE = BASE_DIR / "static" / "current_house.txt"
WINNERS_DIR = BASE_DIR / "winners"
WINNERS_FILE = WINNERS_DIR / "winners.json"

def init_files():
    """Initialize required files and directories"""
    try:
        # Create directories if they don't exist
        os.makedirs(HOUSES_DIR, exist_ok=True)
        os.makedirs(WINNERS_DIR, exist_ok=True)
        
        # Initialize current_house.txt with default value if missing
        if not CURRENT_HOUSE_FILE.exists():
            with open(CURRENT_HOUSE_FILE, 'w') as f:
                f.write("1")  # Default starting house
        
        # Initialize empty winners.json if missing
        if not WINNERS_FILE.exists():
            with open(WINNERS_FILE, 'w') as f:
                json.dump([], f)
                
    except Exception as e:
        print(f"⚠️ Error initializing files: {str(e)}")
        raise

def get_current_house():
    """Get current house number"""
    try:
        with open(CURRENT_HOUSE_FILE, 'r') as f:
            return int(f.read().strip())
    except (ValueError, FileNotFoundError):
        return 1  # Fallback to house1

def get_required_address():
    """Get address for current house"""
    house_num = get_current_house()
    address_file = HOUSES_DIR / f"house{house_num}_address.txt"
    
    try:
        with open(address_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Address not found for house {house_num}"

def normalize_address(address):
    """Standardize address format for comparison"""
    return re.sub(r'[,\s]+', ' ', address.strip()).lower()

def rotate_house():
    """Advance to next house (1-10)"""
    current_num = get_current_house()
    next_num = current_num + 1 if current_num < 10 else 1
    with open(CURRENT_HOUSE_FILE, 'w') as f:
        f.write(str(next_num))
    return next_num

def load_winners():
    """Load all winners from JSON file"""
    try:
        with open(WINNERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []  # Return empty list if file doesn't exist or is invalid

def save_winners(winners):
    """Save winners to JSON file"""
    with open(WINNERS_FILE, 'w') as f:
        json.dump(winners, f, indent=2)

def validate_environment():
    """Validate all required files and directories exist"""
    print("\n=== Environment Validation ===")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Houses Directory: {HOUSES_DIR} (Exists: {HOUSES_DIR.exists()})")
    print(f"Current House File: {CURRENT_HOUSE_FILE} (Exists: {CURRENT_HOUSE_FILE.exists()})")
    print(f"Winners Directory: {WINNERS_DIR} (Exists: {WINNERS_DIR.exists()})")
    print(f"Winners File: {WINNERS_FILE} (Exists: {WINNERS_FILE.exists()})")
    
    print("\nCurrent House Addresses:")
    for i in range(1, 11):
        addr_file = HOUSES_DIR / f"house{i}_address.txt"
        if addr_file.exists():
            with open(addr_file, 'r') as f:
                addr = f.read().strip()
                print(f"House {i}: {addr if addr else '❌ EMPTY'}")
        else:
            print(f"House {i}: ❌ FILE MISSING")

# Initialize application files
init_files()
validate_environment()

# API Endpoints
@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    """Handle address submissions and winner claims"""
    data = request.json
    
    # Address verification phase
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
    
    # Winner details submission
    elif 'name' in data and 'mobile' in data:
        winners = load_winners()
        solved_house = get_current_house()
        solved_address = get_required_address()
        
        # Create winner entry before rotating house
        winner_entry = {
            "name": data.get("name", "").strip(),
            "mobile": data.get("mobile", "").strip(),
            "address": solved_address,
            "houseNumber": solved_house,
            "date": datetime.now().isoformat(),
            "prize": "$10 Woolworths Gift Card"
        }
        
        # Add to winners and save
        winners.append(winner_entry)
        save_winners(winners)
        
        # Rotate to next house
        new_house = rotate_house()
        
        return jsonify({
            "status": "success",
            "next_house": new_house,
            "winnerData": winner_entry
        })

@app.route("/get-current-house")
def current_house():
    """Get current house info"""
    return jsonify({
        "number": get_current_house(),
        "total": 10,
        "address": get_required_address()
    })

@app.route("/get-winners")
def get_winners():
    """Get all winners"""
    return jsonify(load_winners())

@app.route('/')
def serve():
    """Serve main page"""
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    # Print startup info
    print(f"\n🚀 Starting Houseek Server")
    print(f"Current House: {get_current_house()} - {get_required_address()}")
    print(f"Winners Count: {len(load_winners())}")
    
    # Run the app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))