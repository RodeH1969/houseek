from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from pathlib import Path
import re
import json
import shutil

app = Flask(__name__, static_folder='static')
CORS(app)

# ======================
# PERSISTENT STORAGE SETUP
# ======================
PERSISTENT_DIR = Path("/data")  # Render persistent storage
WINNERS_FILE = PERSISTENT_DIR / "winners.json"
BACKUP_FILE = PERSISTENT_DIR / "winners_backup.json"
LOG_FILE = PERSISTENT_DIR / "winners.log"

# Fallback to local storage if persistent not available
if not PERSISTENT_DIR.exists():
    PERSISTENT_DIR = Path("winners")
    
HOUSES_DIR = Path("static/houses")
CURRENT_HOUSE_FILE = Path("static/current_house.txt")

# ======================
# INITIALIZATION
# ======================
def init_files():
    """Initialize with triple redundancy"""
    try:
        os.makedirs(PERSISTENT_DIR, exist_ok=True)
        
        # Initialize files if they don't exist
        if not WINNERS_FILE.exists():
            with open(WINNERS_FILE, 'w') as f:
                json.dump([], f)
        
        # Create backup copy
        shutil.copy2(WINNERS_FILE, BACKUP_FILE)
        
    except Exception as e:
        log_error(f"Initialization failed: {str(e)}")
        raise

# ======================
# DATA PERSISTENCE LAYERS
# ======================        
def save_winners(winners):
    """Save with triple redundancy and atomic writes"""
    try:
        # 1. Write to temp file first
        temp_file = WINNERS_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(winners, f, indent=2)
            
        # 2. Atomic rename (crash-proof)
        temp_file.replace(WINNERS_FILE)
        
        # 3. Immediate backup
        shutil.copy2(WINNERS_FILE, BACKUP_FILE)
        
        # 4. Append to log
        with open(LOG_FILE, 'a') as f:
            f.write(f"{datetime.now()}: Saved {len(winners)} winners\n")
            
    except Exception as e:
        log_error(f"Save failed: {str(e)}")
        raise

def load_winners():
    """Load with automatic recovery"""
    try:
        if not WINNERS_FILE.exists():
            if BACKUP_FILE.exists():
                shutil.copy2(BACKUP_FILE, WINNERS_FILE)
            else:
                return []
                
        with open(WINNERS_FILE, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        log_error(f"Load failed: {str(e)}")
        if BACKUP_FILE.exists():
            return json.load(BACKUP_FILE)
        return []

# ======================
# HOUSE MANAGEMENT
# ======================
def get_max_house_number():
    """Dynamically detect all available houses"""
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
    current_num = get_current_house()
    max_num = get_max_house_number()
    next_num = current_num + 1 if current_num < max_num else 1
    CURRENT_HOUSE_FILE.write_text(str(next_num))
    return next_num

# ======================
# ERROR HANDLING
# ======================
def log_error(message):
    """Robust error logging"""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"ERROR {datetime.now()}: {message}\n")
    except:
        pass  # Last resort fallback

# ======================
# API ENDPOINTS
# ======================
@app.route("/submit-winner", methods=["POST"])
def submit_winner():
    try:
        data = request.json
        
        if 'address' in data:
            # Address verification logic
            pass
            
        elif 'name' in data and 'mobile' in data:
            winners = load_winners()
            current_house = get_current_house()
            
            winners.append({
                "name": data["name"].strip(),
                "mobile": data["mobile"].strip(),
                "address": get_required_address(),
                "houseNumber": current_house,
                "date": datetime.now().isoformat(),
                "prize": "$10 Woolworths Gift Card",
                "ip": request.remote_addr
            })
            
            save_winners(winners)  # Uses bulletproof save
            rotate_house()
            
            return jsonify({"status": "success"})
            
    except Exception as e:
        log_error(f"Submission failed: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to save winner"}), 500

# Other endpoints remain the same...
# (keep your existing /get-current-house, /get-winners, etc.)

if __name__ == "__main__":
    init_files()  # Initialize with redundancy
    print(f"Persistent storage: {PERSISTENT_DIR.absolute()}")
    print(f"Existing winners: {len(load_winners())}")
    app.run(host='0.0.0.0', port=5001)