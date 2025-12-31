from flask import Flask, request, jsonify
import requests
import re
import time
import os

# Initialize Flask app
app = Flask(__name__)

# API Info
API_OWNER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_telegram_username(username):
    """Check if username is taken on Telegram"""
    try:
        url = f"https://t.me/{username}"
        response = requests.get(url, headers=HEADERS, timeout=5)
        
        # Check if it's a Telegram user/channel page
        if "tgme_page" in response.text or "tgme_widget_message" in response.text:
            return True
        # Check if it shows "If you have Telegram" message (available)
        elif "If you have <strong>Telegram</strong>, you can contact" in response.text:
            return False
        return False
    except:
        return False

def check_fragment_username(username):
    """Check if username is on Fragment marketplace"""
    try:
        url = f"https://fragment.com/username/{username}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return {"on_fragment": False}
        
        html = response.text.lower()
        
        # Check for sold
        if "this username was sold" in html or "sold for" in html:
            return {
                "on_fragment": True,
                "status": "Sold",
                "price": self.extract_price(html)
            }
        
        # Check for available
        if "buy username" in html or "place a bid" in html:
            return {
                "on_fragment": True,
                "status": "Available",
                "price": self.extract_price(html)
            }
        
        return {"on_fragment": False}
        
    except:
        return {"on_fragment": False}

def extract_price(html):
    """Extract price from Fragment HTML"""
    try:
        match = re.search(r'(\d[\d,]+)\s*ton', html)
        if match:
            return match.group(1).replace(',', '')
    except:
        pass
    return None

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "api": "Telegram Fragment Username Checker API",
        "author": API_OWNER,
        "contact": CONTACT,
        "endpoints": {
            "/check": "GET /check?username=example",
            "/health": "GET /health",
            "/batch": "POST /batch with JSON {\"usernames\":[...]}"
        },
        "example": "/check?username=tobi",
        "status": "online"
    })

@app.route('/check', methods=['GET'])
def check():
    """Check single username"""
    try:
        username = request.args.get('username', '').replace('@', '').strip().lower()
        
        if not username:
            return jsonify({"error": "Username is required", "example": "/check?username=tobi"}), 400
        
        # Check Telegram
        telegram_taken = check_telegram_username(username)
        
        # Check Fragment
        fragment_data = check_fragment_username(username)
        
        # Determine status
        if telegram_taken:
            status = "Taken on Telegram"
            can_claim = False
        elif fragment_data.get("on_fragment"):
            status = fragment_data.get("status", "Listed on Fragment")
            can_claim = False
        else:
            status = "Available"
            can_claim = True
        
        return jsonify({
            "username": f"@{username}",
            "status": status,
            "telegram_taken": telegram_taken,
            "on_fragment": fragment_data.get("on_fragment", False),
            "price_ton": fragment_data.get("price"),
            "can_claim": can_claim,
            "api_owner": API_OWNER,
            "contact": CONTACT,
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Telegram Username Checker"
    })

@app.route('/batch', methods=['POST'])
def batch():
    """Batch check usernames"""
    try:
        data = request.get_json()
        if not data or 'usernames' not in data:
            return jsonify({"error": "Send JSON with 'usernames' array"}), 400
        
        usernames = data['usernames']
        
        if not isinstance(usernames, list):
            return jsonify({"error": "'usernames' must be an array"}), 400
        
        if len(usernames) > 20:
            return jsonify({"error": "Maximum 20 usernames allowed"}), 400
        
        results = []
        
        for uname in usernames:
            username = str(uname).replace('@', '').strip().lower()
            if username:
                telegram_taken = check_telegram_username(username)
                fragment_data = check_fragment_username(username)
                
                if telegram_taken:
                    status = "Taken on Telegram"
                elif fragment_data.get("on_fragment"):
                    status = fragment_data.get("status", "Listed")
                else:
                    status = "Available"
                
                results.append({
                    "username": f"@{username}",
                    "status": status,
                    "telegram_taken": telegram_taken,
                    "on_fragment": fragment_data.get("on_fragment", False)
                })
        
        return jsonify({
            "results": results,
            "count": len(results),
            "api_owner": API_OWNER
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# CORS middleware for Vercel
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Vercel requires this
if __name__ == '__main__':
    app.run(debug=True)
else:
    # For Vercel serverless
    application = app
