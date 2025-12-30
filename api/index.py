from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def telegram_taken(username):
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False

def fragment_check(username):
    try:
        url = f"https://fragment.com/username/{username}"
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        price = None
        status = "Available"

        price_tag = soup.select_one(".tm-section-header__subtitle")
        if price_tag:
            price = price_tag.text.replace("TON", "").strip()

        if "Sold" in r.text:
            status = "Sold"

        return {
            "price": price,
            "status": status,
            "url": url
        }
    except:
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "Fragment Username Check API",
        "usage": "/check?username=aotpy",
        "status": "running"
    })

@app.route("/check", methods=["GET"])
def check():
    username = request.args.get("username", "").replace("@", "").lower()

    if not username:
        return jsonify({"error": "username parameter required"}), 400

    if telegram_taken(username):
        return jsonify({
            "username": f"@{username}",
            "price_ton": "Unknown",
            "status": "Taken",
            "can_claim": False,
            "message": ""
        })

    fragment = fragment_check(username)

    if fragment:
        return jsonify({
            "username": f"@{username}",
            "price_ton": fragment["price"] or "Unknown",
            "status": fragment["status"],
            "can_claim": False,
            "message": "Buy from Fragment" if fragment["price"] else "",
            "fragment_url": fragment["url"]
        })

    return jsonify({
        "username": f"@{username}",
        "price_ton": "Unknown",
        "status": "Available",
        "can_claim": True,
        "message": "Can be claimed directly"
    })

app = app
