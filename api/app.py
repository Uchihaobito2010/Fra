# app.py
from flask import Flask, request, jsonify
import requests
import re
import time
from functools import lru_cache
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

API_OWNER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app/"
CHANNEL = "@obitoapi / @obitostuffs"

# ---------------- UTILITY FUNCTIONS ----------------
def validate_username(username):
    """Validate Telegram username format"""
    if not username or len(username) < 5 or len(username) > 32:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

# ---------------- TELEGRAM CHECK ----------------
@lru_cache(maxsize=100)
def is_telegram_taken(username):
    """Check if username is taken on Telegram"""
    try:
        url = f"https://t.me/{username}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check for "If you have Telegram, you can contact" - indicates available username
        if "If you have <strong>Telegram</strong>, you can contact" in r.text:
            return False
            
        # Check if it's a valid Telegram page
        if "tgme_page" in r.text or "tgme_widget_message" in r.text:
            return True
            
        return False
    except Exception as e:
        logger.error(f"Telegram check error for {username}: {e}")
        return None  # Return None on error

# ---------------- FRAGMENT CHECK ----------------
@lru_cache(maxsize=100)
def fragment_lookup(username):
    """Check if username is on Fragment marketplace"""
    url = f"https://fragment.com/username/{username}"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        # If page doesn't exist, username not on Fragment
        if r.status_code == 404:
            return {"on_fragment": False, "status": "Not Found"}
            
        if r.status_code != 200:
            return {"on_fragment": False, "status": "Error", "error_code": r.status_code}
        
        html = r.text.lower()
        
        # ---------- SOLD DETECTION ----------
        sold_keywords = [
            "this username was sold",
            "sold for",
            "final price",
            "this lot is sold",
            "auction ended",
            "was purchased"
        ]
        
        for keyword in sold_keywords:
            if keyword in html:
                # Extract price if available
                price_match = re.search(r'(\d[\d,]+\s*ton)', html)
                price = price_match.group(1).replace(',', '') if price_match else None
                
                return {
                    "on_fragment": True,
                    "status": "Sold",
                    "price": price,
                    "url": url,
                    "fragment_type": "username"
                }
        
        # ---------- AVAILABLE ON FRAGMENT ----------
        available_keywords = [
            "buy username",
            "place a bid",
            "current bid",
            "starting price",
            "auction ends",
            "fragment marketplace"
        ]
        
        for keyword in available_keywords:
            if keyword in html:
                # Extract price
                price_match = re.search(r'(\d[\d,]+)\s*ton', html)
                price = price_match.group(1).replace(',', '') if price_match else None
                
                # Check if it's auction or fixed price
                if "auction ends" in html or "place a bid" in html:
                    status = "Auction"
                else:
                    status = "Available for Purchase"
                
                return {
                    "on_fragment": True,
                    "status": status,
                    "price": price,
                    "url": url,
                    "fragment_type": "username"
                }
        
        # ---------- RESERVED/PREMIUM ----------
        if "reserved" in html or "premium" in html:
            return {
                "on_fragment": True,
                "status": "Reserved/Premium",
                "price": None,
                "url": url,
                "fragment_type": "username"
            }
        
        # ---------- NOT ON FRAGMENT ----------
        return {"on_fragment": False, "status": "Not Listed"}
        
    except Exception as e:
        logger.error(f"Fragment lookup error for {username}: {e}")
        return {"on_fragment": False, "status": "Error", "error": str(e)}

# ---------------- BATCH CHECK ----------------
def batch_check_usernames(usernames):
    """Check multiple usernames at once"""
    results = []
    for username in usernames:
        if validate_username(username):
            result = check_single_username(username)
            results.append(result)
    return results

# ---------------- SINGLE CHECK LOGIC ----------------
def check_single_username(username):
    """Core checking logic for a single username"""
    username = username.replace("@", "").strip().lower()
    
    # Validate username
    if not validate_username(username):
        return {
            "username": f"@{username}",
            "status": "Invalid",
            "price_ton": None,
            "on_fragment": False,
            "can_claim": False,
            "message": "Invalid Telegram username format",
            "valid": False
        }
    
    # Check Telegram
    telegram_status = is_telegram_taken(username)
    
    # If Telegram check failed
    if telegram_status is None:
        return {
            "username": f"@{username}",
            "status": "Unknown",
            "price_ton": None,
            "on_fragment": False,
            "can_claim": False,
            "message": "Unable to check Telegram status",
            "valid": True
        }
    
    # If taken on Telegram
    if telegram_status:
        return {
            "username": f"@{username}",
            "status": "Taken on Telegram",
            "price_ton": None,
            "on_fragment": False,
            "can_claim": False,
            "message": "Username is already in use on Telegram",
            "valid": True
        }
    
    # Check Fragment
    fragment = fragment_lookup(username)
    
    if fragment.get("on_fragment"):
        message_map = {
            "Sold": "This username was sold on Fragment",
            "Auction": "Available for auction on Fragment",
            "Available for Purchase": "Available for purchase on Fragment",
            "Reserved/Premium": "Reserved or premium username on Fragment"
        }
        
        return {
            "username": f"@{username}",
            "status": fragment.get("status"),
            "price_ton": fragment.get("price"),
            "on_fragment": True,
            "can_claim": False,
            "message": message_map.get(fragment.get("status"), "Listed on Fragment"),
            "fragment_url": fragment.get("url"),
            "valid": True
        }
    
    # Available for claim
    return {
        "username": f"@{username}",
        "status": "Available",
        "price_ton": None,
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly on Telegram",
        "valid": True
    }

# ---------------- ENHANCED FRAGMENT API CHECK ----------------
def fragment_api_check(username):
    """Alternative check using Fragment API"""
    try:
        # First get the homepage to find API hash
        r = requests.get("https://fragment.com", headers=HEADERS, timeout=10)
        
        # Find API hash in JavaScript
        hash_match = re.search(r'hash=([a-fA-F0-9]+)', r.text)
        if not hash_match:
            return None
            
        api_url = f"https://fragment.com/api?hash={hash_match.group(1)}"
        
        # Prepare API request
        data = {
            "type": "usernames",
            "query": username,
            "method": "searchAuctions"
        }
        
        api_response = requests.post(api_url, data=data, headers=HEADERS, timeout=10)
        return api_response.json()
        
    except Exception as e:
        logger.error(f"Fragment API error: {e}")
        return None

# ---------------- ENDPOINTS ----------------

@app.route("/", methods=["GET"])
def home():
    """API homepage with documentation"""
    return jsonify({
        "api": "Telegram Username Availability Checker",
        "version": "2.0",
        "author": API_OWNER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL,
        "endpoints": {
            "/check": "Check single username (GET: ?username=xxx)",
            "/batch": "Check multiple usernames (POST: JSON array)",
            "/health": "API health check",
            "/validate": "Validate username format (GET: ?username=xxx)",
            "/status": "API status and usage"
        },
        "example": "/check?username=tobi",
        "note": "All usernames should be without @ symbol",
        "status": "online",
        "timestamp": time.time()
    })

@app.route("/check", methods=["GET"])
def check_username():
    """Check availability of a single username"""
    username = request.args.get("username", "").replace("@", "").strip()
    
    if not username:
        return jsonify({
            "error": "Username is required",
            "example": "/check?username=example"
        }), 400
    
    result = check_single_username(username)
    result.update({
        "api_owner": API_OWNER,
        "contact": CONTACT,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    })
    
    return jsonify(result)

@app.route("/batch", methods=["POST"])
def batch_check():
    """Check multiple usernames at once"""
    try:
        data = request.get_json()
        if not data or "usernames" not in data:
            return jsonify({
                "error": "Please provide 'usernames' array in JSON body",
                "example": {"usernames": ["user1", "user2", "user3"]}
            }), 400
        
        usernames = data["usernames"]
        if not isinstance(usernames, list) or len(usernames) > 50:
            return jsonify({
                "error": "Please provide up to 50 usernames in an array"
            }), 400
        
        results = batch_check_usernames(usernames)
        
        return jsonify({
            "results": results,
            "total": len(results),
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "api_owner": API_OWNER
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/validate", methods=["GET"])
def validate_endpoint():
    """Validate username format"""
    username = request.args.get("username", "").replace("@", "").strip()
    
    if not username:
        return jsonify({
            "error": "Username is required",
            "example": "/validate?username=example"
        }), 400
    
    is_valid = validate_username(username)
    
    return jsonify({
        "username": f"@{username}",
        "valid": is_valid,
        "rules": {
            "min_length": 5,
            "max_length": 32,
            "allowed_chars": "a-z, A-Z, 0-9, _",
            "no_spaces": True
        },
        "message": "Valid Telegram username" if is_valid else "Invalid Telegram username format"
    })

@app.route("/health", methods=["GET"])
def health_check():
    """API health check endpoint"""
    # Test both services
    telegram_test = is_telegram_taken("telegram") is not None
    fragment_test = fragment_lookup("telegram") is not None
    
    return jsonify({
        "status": "healthy" if telegram_test and fragment_test else "degraded",
        "services": {
            "telegram_check": "operational" if telegram_test else "degraded",
            "fragment_check": "operational" if fragment_test else "degraded"
        },
        "timestamp": time.time(),
        "uptime": "N/A"  # Could use process time if needed
    })

@app.route("/status", methods=["GET"])
def status():
    """API status and usage statistics"""
    return jsonify({
        "api": "Telegram Username Checker",
        "status": "operational",
        "version": "2.0",
        "features": [
            "Telegram username availability check",
            "Fragment.com marketplace status",
            "Batch processing",
            "Username validation",
            "Real-time checking"
        ],
        "rate_limits": "No limits applied",
        "cache": "Enabled (LRU cache with 100 entries)",
        "author": API_OWNER,
        "contact": CONTACT
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/check", "/batch", "/health", "/validate", "/status"]
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "error": "Internal server error",
        "contact": CONTACT
    }), 500

# For Vercel deployment
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
