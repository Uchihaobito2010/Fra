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
def is_telegram_taken(username: str) -> bool:
    try:
        r = requests.get(
            f"https://t.me/{username}",
            headers=HEADERS,
            timeout=10
        )
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


# ---------------- FRAGMENT CHECK ----------------
def fragment_lookup(username: str):
    try:
        url = f"https://fragment.com/username/{username}"
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code != 200:
            return {"listed": False}

        html = r.text.lower()

        # SOLD username
        if "sold" in html:
            return {
                "listed": True,
                "status": "Sold",
                "price": None,
                "url": url
            }

        # AVAILABLE on fragment (price detection)
        price_match = re.search(r'([\d,]{3,})\s*ton', html)
        if price_match:
            return {
                "listed": True,
                "status": "Available",
                "price": price_match.group(1).replace(",", ""),
                "url": url
            }

        # Page exists but username NOT listed on fragment
        return {"listed": False}

    except:
        return {"listed": False}


# ---------------- ROOT ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Telegram Fragment Username Check API",
        "usage": "/check?username=aotpy",
        "status": "online"
    })


# ---------------- MAIN ENDPOINT ----------------
@app.route("/check", methods=["GET"])
def check_username():
    username = request.args.get("username", "").replace("@", "").lower()

    if not username:
        return jsonify({"error": "username parameter required"}), 400

    # Step 1: Telegram username taken?
    if is_telegram_taken(username):
        return jsonify({
            "username": f"@{username}",
            "price_ton": "Unknown",
            "status": "Taken",
            "on_fragment": False,
            "can_claim": False,
            "message": ""
        })

    # Step 2: Fragment lookup
    fragment = fragment_lookup(username)

    if fragment.get("listed"):
        return jsonify({
            "username": f"@{username}",
            "price_ton": fragment.get("price") or "Unknown",
            "status": fragment.get("status"),
            "on_fragment": True,
            "can_claim": False,
            "message": "Buy from Fragment" if fragment.get("price") else "",
            "fragment_url": fragment.get("url")
        })

    # Step 3: Fully claimable
    return jsonify({
        "username": f"@{username}",
        "price_ton": "Unknown",
        "status": "Available",
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly"
    })


app = app
