from flask import Flask, request, jsonify
import requests
import re
import time

app = Flask(__name__)

API_OWNER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"
CHANNEL = "@obitoapi / @obitostuffs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "api": "Telegram Fragment Username Checker",
        "author": API_OWNER,
        "contact": CONTACT,
        "endpoints": {
            "/check": "Check username - GET /check?username=xxx",
            "/batch": "Batch check - POST /batch with JSON {\"usernames\":[...]}",
            "/health": "Health check"
        },
        "example": "/check?username=tobi"
    })

@app.route('/check', methods=['GET'])
def check():
    username = request.args.get('username', '').replace('@', '').strip().lower()
    
    if not username:
        return jsonify({"error": "Username is required", "example": "/check?username=tobi"}), 400
    
    # Telegram check
    telegram_taken = check_telegram(username)
    
    # Fragment check
    fragment_data = check_fragment(username)
    
    if telegram_taken:
        status = "Taken on Telegram"
        can_claim = False
    elif fragment_data.get("on_fragment"):
        status = fragment_data.get("status", "On Fragment")
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
        "fragment_url": fragment_data.get("url"),
        "api_owner": API_OWNER,
        "contact": CONTACT,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    })

@app.route('/batch', methods=['POST'])
def batch():
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        
        if not usernames or len(usernames) > 50:
            return jsonify({"error": "Provide up to 50 usernames in array"}), 400
        
        results = []
        for username in usernames:
            username = str(username).replace('@', '').strip().lower()
            
            if username:
                telegram_taken = check_telegram(username)
                fragment_data = check_fragment(username)
                
                results.append({
                    "username": f"@{username}",
                    "telegram_taken": telegram_taken,
                    "on_fragment": fragment_data.get("on_fragment", False),
                    "status": fragment_data.get("status", "Not on Fragment")
                })
        
        return jsonify({
            "results": results,
            "total": len(results),
            "api_owner": API_OWNER
        })
    except:
        return jsonify({"error": "Invalid JSON format"}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Telegram Username Checker"
    })

def check_telegram(username):
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=5)
        return "tgme_page" in r.text or "tgme_widget_message" in r.text
    except:
        return False

def check_fragment(username):
    url = f"https://fragment.com/username/{username}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        html = r.text.lower()
        
        if "this username was sold" in html:
            return {"on_fragment": True, "status": "Sold", "url": url}
        
        if "buy username" in html or "place a bid" in html:
            price_match = re.search(r'(\d[\d,]+)\s*ton', html)
            price = price_match.group(1).replace(',', '') if price_match else None
            return {"on_fragment": True, "status": "Available", "price": price, "url": url}
        
        return {"on_fragment": False}
    except:
        return {"on_fragment": False}

if __name__ == '__main__':
    app.run()
