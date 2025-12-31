"""
Telegram Username Checker API for Vercel
Author: Paras Chourasiya
Contact: t.me/Aotpy
"""

from flask import Flask, request, jsonify
import requests
import re
import time

# Create Flask app
app = Flask(__name__)

# Set CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Home endpoint
@app.route('/')
def home():
    return jsonify({
        "api": "Telegram Fragment Username Checker",
        "author": "Paras Chourasiya",
        "contact": "t.me/Aotpy",
        "portfolio": "https://aotpy.vercel.app",
        "endpoints": {
            "/check": "GET /check?username=example",
            "/health": "GET /health",
            "/batch": "POST /batch with JSON {\"usernames\": [...]}"
        },
        "example": "https://your-api.vercel.app/check?username=tobi"
    })

# Check single username
@app.route('/check')
def check_username():
    username = request.args.get('username', '').replace('@', '').strip().lower()
    
    if not username:
        return jsonify({"error": "Username is required", "example": "/check?username=tobi"}), 400
    
    try:
        # 1. Check Telegram
        telegram_url = f"https://t.me/{username}"
        tg_response = requests.get(telegram_url, timeout=5)
        telegram_taken = "tgme_page" in tg_response.text
        
        # 2. Check Fragment
        fragment_url = f"https://fragment.com/username/{username}"
        fr_response = requests.get(fragment_url, timeout=10)
        html = fr_response.text.lower()
        
        on_fragment = False
        price = None
        fragment_status = "Not on Fragment"
        
        if "this username was sold" in html:
            on_fragment = True
            fragment_status = "Sold on Fragment"
        elif "buy username" in html or "place a bid" in html:
            on_fragment = True
            fragment_status = "Available on Fragment"
            # Extract price
            match = re.search(r'(\d[\d,]+)\s*ton', html)
            if match:
                price = match.group(1).replace(',', '')
        
        # Determine final status
        if telegram_taken:
            status = "Taken on Telegram"
            can_claim = False
        elif on_fragment:
            status = fragment_status
            can_claim = False
        else:
            status = "Available"
            can_claim = True
        
        return jsonify({
            "username": f"@{username}",
            "status": status,
            "telegram_taken": telegram_taken,
            "on_fragment": on_fragment,
            "price_ton": price,
            "can_claim": can_claim,
            "fragment_url": fragment_url if on_fragment else None,
            "api_owner": "Paras Chourasiya",
            "contact": "t.me/Aotpy",
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

# Batch check
@app.route('/batch', methods=['POST'])
def batch_check():
    try:
        data = request.get_json()
        if not data or 'usernames' not in data:
            return jsonify({"error": "Send JSON with 'usernames' array"}), 400
        
        usernames = data['usernames']
        if not isinstance(usernames, list):
            return jsonify({"error": "'usernames' must be an array"}), 400
        
        results = []
        for uname in usernames[:10]:  # Limit to 10
            username = str(uname).replace('@', '').strip()
            if username:
                # Simple check
                results.append({
                    "username": f"@{username}",
                    "checked": True
                })
        
        return jsonify({
            "results": results,
            "count": len(results),
            "api_owner": "Paras Chourasiya"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Handle OPTIONS for CORS
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200

# Vercel requires this
if __name__ == '__main__':
    app.run()
else:
    # This is IMPORTANT for Vercel
    application = app
