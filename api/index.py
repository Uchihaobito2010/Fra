from flask import Flask, request, jsonify
import requests, re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

# ---------- CHECK TELEGRAM ----------
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


# ---------- CHECK FRAGMENT ----------
def fragment_lookup(username: str):
    try:
        url = f"https://fragment.com/username/{username}"
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code != 200:
            return None

        html = r.text

        # Extract TON price
        price = None
        price_match = re.search(r'([\d,]+)\s*TON', html)
        if price_match:
            price = price_match.group(1).replace(",", "")

        # Status
        status = "Available"
        if "Sold" in html:
            status = "Sold"

        return {
            "price": price,
            "status": status,
            "url": url
        }

    except:
        return None


# ---------- ROOT ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Fragment Username Check API",
        "usage": "/check?username=aotpy",
        "status": "online"
    })


# ---------- MAIN ENDPOINT ----------
@app.route("/check", methods=["GET"])
def check_username():
    username = request.args.get("username", "").replace("@", "").lower()

    if not username:
        return jsonify({"error": "username parameter required"}), 400

    # Step 1: Telegram check
    if is_telegram_taken(username):
        return jsonify({
            "username": f"@{username}",
            "price_ton": "Unknown",
            "status": "Taken",
            "on_fragment": False,
            "can_claim": False,
            "message": ""
        })

    # Step 2: Fragment check
    fragment = fragment_lookup(username)

    if fragment:
        return jsonify({
            "username": f"@{username}",
            "price_ton": fragment["price"] or "Unknown",
            "status": fragment["status"],
            "on_fragment": True,
            "can_claim": False,
            "message": "Buy from Fragment" if fragment["price"] else "",
            "fragment_url": fragment["url"]
        })

    # Step 3: Fully available
    return jsonify({
        "username": f"@{username}",
        "price_ton": "Unknown",
        "status": "Available",
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly"
    })


app = app
