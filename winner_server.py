from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re
import json
import shutil

# Initialize Flask app with correct static file handling
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
        # Create necessary directories
        os.makedirs(PERSISTENT_DIR, exist_ok=True)
        os.makedirs(HOUSES_DIR, exist_ok=True)
        
        # Initialize winners file if missing
        if not WINNERS_FILE.exists():
            with open(WINNERS_FILE, 'w') as f:
                json.dump([], f)
        
        # Create initial backup
        shutil.copy2(WINNERS_FILE, BACKUP_FILE)
        
        # Verify static files exist
        if not (BASE_DIR / "static/index.html").exists():
            raise FileNotFoundError("index.html not found in static/")
            
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        raise

# ======================
# DATA PERSISTENCE
# ======================
def save_winners(winners):
    """Save winners with crash protection"""
    try:
        # 1. Write to temp file
        temp_path = WINNERS_FILE.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(winners, f, indent=2)
        
        # 2. Atomic replace
        temp_path.replace(WINNERS_FILE)
        
        # 3. Create backup
        shutil.copy2(WINNERS_FILE, BACKUP_FILE)
        
        # 4. Log operation
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
# HOUSE MANAGEMENT
# ======================
def get_max_house_number():
    """Dynamically find highest house number"""
    max_num = 0
    for file in os.listdir(HOUSES_DIR):
        if file.startswith('house') and file.endswith('.png'):
            try:
                num = int(file[5:-4])
                max_num = max(max_num, num)
            except ValueError:
                continue
    return max_num if max_num > 0 else 1

def get_current_house():
    try:
        return int(CURRENT_HOUSE_FILE.read_text())
    except:
        return 1

def rotate_house():
    current = get_current_house()
    max_num = get_max_house_number()
    next_num = current + 1 if current < max_num else 1
    CURRENT_HOUSE_FILE.write_text(str(next_num))
    return next_num

def get_required_address():
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
    """Serve the main index.html"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    try:
        data = request.json
        
        if 'address' in data:
            # Address verification
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
            # Winner submission
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
        "total": get_max_house_number(),
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
    print(f"Server initialized with {get_max_house_number()} houses")
    print(f"Static files served from: {app.static_folder}")
    print(f"Persistent storage at: {PERSISTENT_DIR}")
    app.run(host='0.0.0.0', port=5001)