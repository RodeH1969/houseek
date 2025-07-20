from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re
import json
import shutil

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ======================
# PATH CONFIGURATION
# ======================
BASE_DIR = Path(__file__).parent.absolute()
PERSISTENT_DIR = Path("/data") if Path("/data").exists() else BASE_DIR / "winners"

# Core paths
HOUSES_DIR = BASE_DIR / "static/houses"
CURRENT_HOUSE_FILE = BASE_DIR / "static/current_house.txt"
WINNERS_FILE = PERSISTENT_DIR / "winners.json"
BACKUP_FILE = PERSISTENT_DIR / "winners_backup.json"
LOG_FILE = PERSISTENT_DIR / "winners.log"

# ======================
# INITIALIZATION
# ======================
def init_storage():
    """Initialize all required directories and files"""
    try:
        os.makedirs(PERSISTENT_DIR, exist_ok=True)
        os.makedirs(HOUSES_DIR, exist_ok=True)
        
        if not WINNERS_FILE.exists():
            with open(WINNERS_FILE, 'w') as f:
                json.dump([], f)
        
        if not CURRENT_HOUSE_FILE.exists():
            CURRENT_HOUSE_FILE.write_text("1")
            
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        raise

# ======================
# DATA PERSISTENCE
# ======================
def save_winners(winners):
    """Save winners with crash protection"""
    try:
        temp_path = WINNERS_FILE.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(winners, f, indent=2)
        
        temp_path.replace(WINNERS_FILE)
        shutil.copy2(WINNERS_FILE, BACKUP_FILE)
        
        with open(LOG_FILE, 'a') as f:
            f.write(f"{datetime.now()}: Saved {len(winners)} winners\n")
            
    except Exception as e:
        print(f"Failed to save winners: {str(e)}")
        raise

def load_winners():
    """Load winners with automatic recovery"""
    try:
        if not WINNERS_FILE.exists():
            if BACKUP_FILE.exists():
                shutil.copy2(BACKUP_FILE, WINNERS_FILE)
            return []
            
        with open(WINNERS_FILE, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"Failed to load winners: {str(e)}")
        if BACKUP_FILE.exists():
            return json.load(BACKUP_FILE)
        return []

# ======================
# HOUSE MANAGEMENT (FIXED)
# ======================
def get_all_house_numbers():
    """Get all valid house numbers including special cases (-1, 0)"""
    numbers = []
    for file in os.listdir(HOUSES_DIR):
        if file.startswith('house') and (file.endswith('.png') or file.endswith('_mobile.png')):
            try:
                # Extract number from filename
                base = file.split('.')[0].replace('_mobile', '')
                num_str = base[5:]  # Get everything after 'house'
                
                # Handle special cases
                if num_str == '-1':
                    numbers.append(-1)
                elif num_str == '0':
                    numbers.append(0)
                else:
                    numbers.append(int(num_str))
            except:
                continue
    
    return sorted(list(set(numbers)))

def get_max_house_number():
    """Get highest regular house number (excluding special cases)"""
    numbers = [n for n in get_all_house_numbers() if n > 0]
    return max(numbers) if numbers else 1

def get_current_house():
    """Get current house number including special cases"""
    try:
        return int(CURRENT_HOUSE_FILE.read_text())
    except:
        return 1

def rotate_house():
    """Rotate to next house, handling special cases"""
    current = get_current_house()
    all_houses = get_all_house_numbers()
    
    if not all_houses:
        return 1
    
    # Find current index
    try:
        current_idx = all_houses.index(current)
    except ValueError:
        current_idx = -1
    
    # Get next house (wrap around if needed)
    next_idx = (current_idx + 1) % len(all_houses)
    next_house = all_houses[next_idx]
    
    CURRENT_HOUSE_FILE.write_text(str(next_house))
    return next_house

def get_required_address():
    """Get address for current house (including special cases)"""
    house_num = get_current_house()
    address_file = HOUSES_DIR / f"house{house_num}_address.txt"
    
    if not address_file.exists():
        return f"Address not found for house {house_num}"
        
    return address_file.read_text().strip()

def normalize_address(address):
    return re.sub(r'[,\s]+', ' ', address.strip()).lower()

# ======================
# ROUTES
# ======================
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    try:
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
            house_num = get_current_house()
            
            winners.append({
                "name": data["name"].strip(),
                "mobile": data["mobile"].strip(),
                "address": get_required_address(),
                "houseNumber": house_num,
                "date": datetime.now().isoformat(),
                "prize": "$10 Woolworths Gift Card",
                "ip": request.remote_addr
            })
            
            save_winners(winners)
            new_house = rotate_house()
            
            return jsonify({
                "status": "success",
                "next_house": new_house,
                "winnerData": {
                    "name": data["name"].strip(),
                    "address": get_required_address(),
                    "houseNumber": house_num
                }
            })
            
    except Exception as e:
        print(f"Winner submission error: {str(e)}")
        return jsonify({"status": "error", "message": "Submission failed"}), 500

@app.route("/get-current-house")
def current_house():
    return jsonify({
        "number": get_current_house(),
        "total": len(get_all_house_numbers()),
        "address": get_required_address()
    })

@app.route("/get-winners")
def get_winners_endpoint():
    return jsonify(load_winners())

# ======================
# STARTUP
# ======================
if __name__ == "__main__":
    init_storage()
    print(f"Available house numbers: {get_all_house_numbers()}")
    print(f"Current house: {get_current_house()}")
    app.run(host='0.0.0.0', port=5001)