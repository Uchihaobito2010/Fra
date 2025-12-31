from flask import Flask, request, jsonify
import requests
import re
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# API Info
API_OWNER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"

def check_single_username(username):
    """Core function to check a single username"""
    username = username.replace('@', '').strip().lower()
    
    if not username:
        return {"error": "Username is empty"}
    
    # Check Telegram
    telegram_url = f"https://t.me/{username}"
    try:
        tg_response = requests.get(telegram_url, timeout=5)
        telegram_taken = "tgme_page" in tg_response.text
    except:
        telegram_taken = False
    
    # Check Fragment
    fragment_url = f"https://fragment.com/username/{username}"
    on_fragment = False
    price = None
    fragment_status = "Not on Fragment"
    
    try:
        fr_response = requests.get(fragment_url, timeout=10)
        html = fr_response.text.lower()
        
        if "this username was sold" in html:
            on_fragment = True
            fragment_status = "Sold on Fragment"
        elif "buy username" in html or "place a bid" in html:
            on_fragment = True
            fragment_status = "Available on Fragment"
            price_match = re.search(r'(\d[\d,]+)\s*ton', html)
            if price_match:
                price = price_match.group(1).replace(',', '')
    except:
        pass
    
    # Determine final status
    if telegram_taken:
        final_status = "Taken on Telegram"
        can_claim = False
    elif on_fragment:
        final_status = fragment_status
        can_claim = False
    else:
        final_status = "Available"
        can_claim = True
    
    return {
        "username": f"@{username}",
        "status": final_status,
        "telegram_taken": telegram_taken,
        "on_fragment": on_fragment,
        "price_ton": price,
        "can_claim": can_claim,
        "fragment_url": fragment_url if on_fragment else None,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

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
        "example": "https://yourapi.vercel.app/check?username=tobi",
        "status": "online"
    })

@app.route('/check', methods=['GET'])
def check_username():
    username = request.args.get('username', '').replace('@', '').strip().lower()
    
    if not username:
        return jsonify({"error": "Username is required", "example": "/check?username=tobi"}), 400
    
    result = check_single_username(username)
    result["api_owner"] = API_OWNER
    result["contact"] = CONTACT
    
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Telegram Username Checker API"
    })

@app.route('/batch', methods=['POST'])
def batch_check():
    try:
        data = request.get_json()
        if not data or 'usernames' not in data:
            return jsonify({"error": "Send JSON with 'usernames' array", "example": {"usernames": ["user1", "user2"]}}), 400
        
        usernames = data['usernames']
        
        if not isinstance(usernames, list):
            return jsonify({"error": "'usernames' must be an array"}), 400
        
        if len(usernames) > 50:
            return jsonify({"error": "Maximum 50 usernames allowed"}), 400
        
        results = []
        
        for uname in usernames:
            if uname:  # Skip empty usernames
                result = check_single_username(str(uname))
                results.append(result)
        
        return jsonify({
            "results": results,
            "count": len(results),
            "api_owner": API_OWNER,
            "batch_completed": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        
    except Exception as e:
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

# This is required for Vercel
if __name__ == '__main__':
    app.run()
else:
    # For Vercel serverless
    application = app
