from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

# ---------------- TELEGRAM CHECK ----------------
def is_telegram_taken(username):
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


# ---------------- FRAGMENT CHECK ----------------
def fragment_lookup(username):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"on_fragment": False}

        html = r.text.lower()

        # ---------- STRICT SOLD DETECTION ----------
        sold_signals = [
            "this username was sold",
            "sold for",
            "final price"
        ]

        if any(sig in html for sig in sold_signals):
            return {
                "on_fragment": True,
                "status": "Sold",
                "price": None,
                "url": url
            }

        # ---------- PRICE (OPTIONAL) ----------
        price = None
        m = re.search(r'([\d,]{3,})\s*ton', html)
        if m:
            price = m.group(1).replace(",", "")

        # ---------- LISTED ON FRAGMENT ----------
        fragment_signals = [
            "buy username",
            "place a bid",
            "fragment marketplace"
        ]

        if any(sig in html for sig in fragment_signals):
            return {
                "on_fragment": True,
                "status": "Available",
                "price": price,
                "url": url
            }

        # ---------- NOT ON FRAGMENT ----------
        return {"on_fragment": False}

    except:
        return {"on_fragment": False}


# ---------------- ROOT ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api_owner": "Paras chourasiya",
        "Contact": "t.me/Aotpy",
        "Portfolio": "https://aotpy.vercel.app/",
        
        "api": "Telegram Fragment Username Check API",
        "usage": "/check?username=tobi",
        "status": "online"
    })


# ---------------- MAIN ENDPOINT ----------------
@app.route("/check", methods=["GET"])
def check_username():
    username = request.args.get("username", "").replace("@", "").lower()
    if not username:
        return jsonify({"error": "username required"}), 400

    # 1️⃣ Telegram taken
    if is_telegram_taken(username):
        return jsonify({
            "api_owner": "Paras chourasiya",
            "if any problem contact": "@Aotpy",
            
            "username": f"@{username}",
            "status": "Taken",
            "price_ton": "Unknown",
            "on_fragment": False,
            "can_claim": False,
            "message": ""
        })

    # 2️⃣ Fragment check
    fragment = fragment_lookup(username)

    if fragment.get("on_fragment"):
        return jsonify({
            "owner": "Paras chourasiya",
            "if any problem contact": "@Aotpy",
            
            "username": f"@{username}",
            "status": fragment.get("status"),
            "price_ton": fragment.get("price") or "Unknown",
            "on_fragment": True,
            "can_claim": False,
            "message": "Buy from Fragment" if fragment.get("status") == "Available" else "",
            "fragment_url": fragment.get("url")
        })

    # 3️⃣ Claimable
    return jsonify({
        "api_owner": "Paras chourasiya",
        "if any problem contact": "@Aotpy",
        "username": f"@{username}",
        "status": "Available",
        "price_ton": "Unknown",
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly"
    })


app = app
