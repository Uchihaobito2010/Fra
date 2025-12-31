from flask import Flask, request, jsonify
import requests
import re
import json

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

# ---------------- TON LIVE PRICE ----------------
def get_ton_rate():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "the-open-network",
                "vs_currencies": "usd,inr"
            },
            timeout=10
        )
        data = r.json().get("the-open-network", {})
        return data.get("usd"), data.get("inr")
    except:
        return None, None


# ---------------- TELEGRAM CHECK ----------------
def is_telegram_taken(username):
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


# ---------------- EXTRACT PRICE FROM NEXT_DATA ----------------
def extract_price_from_next_data(html):
    try:
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.DOTALL
        )
        if not m:
            return None

        data = json.loads(m.group(1))

        # deep search for "price"
        def find_price(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "price" and isinstance(v, (int, float)):
                        return float(v)
                    res = find_price(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for i in obj:
                    res = find_price(i)
                    if res:
                        return res
            return None

        return find_price(data)

    except:
        return None


# ---------------- FRAGMENT CHECK ----------------
def fragment_lookup(username):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"on_fragment": False}

        html_raw = r.text
        html = html_raw.lower()

        # SOLD CHECK
        if any(x in html for x in ["this username was sold", "sold for", "final price"]):
            return {
                "on_fragment": True,
                "status": "Sold",
                "price_ton": None,
                "url": url
            }

        # PRICE (REAL METHOD)
        price_ton = extract_price_from_next_data(html_raw)

        # FALLBACK (rare)
        if not price_ton:
            m = re.search(r'([\d,]{2,})\s*ton', html)
            if m:
                price_ton = float(m.group(1).replace(",", ""))

        # LISTED
        if any(x in html for x in ["buy username", "place a bid", "fragment marketplace"]):
            return {
                "on_fragment": True,
                "status": "Available",
                "price_ton": price_ton,
                "url": url
            }

        return {"on_fragment": False}

    except:
        return {"on_fragment": False}


# ---------------- ROOT ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api_owner": "Paras chourasiya",
        "Contact": "t.me/Aotpy",
        "Portfolio": "https://Aotpy.netlify.app",
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

    ton_usd, ton_inr = get_ton_rate()

    # 1️⃣ Telegram taken
    if is_telegram_taken(username):
        return jsonify({
            "api_owner": "Paras chourasiya",
            "contact": "@Aotpy",
            "username": f"@{username}",
            "status": "Taken",
            "on_fragment": False,
            "can_claim": False,
            "price": None
        })

    # 2️⃣ Fragment
    fragment = fragment_lookup(username)

    if fragment.get("on_fragment"):
        price = None
        if fragment.get("price_ton") and ton_usd:
            price = {
                "ton": fragment["price_ton"],
                "usd": round(fragment["price_ton"] * ton_usd, 2),
                "inr": round(fragment["price_ton"] * ton_inr, 2) if ton_inr else None
            }

        return jsonify({
            "api_owner": "Paras chourasiya",
            "contact": "@Aotpy",
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "can_claim": False,
            "price": price,
            "fragment_url": fragment.get("url"),
            "note": "TON price calculated using live market rate"
        })

    # 3️⃣ Claimable
    return jsonify({
        "api_owner": "Paras chourasiya",
        "contact": "@Aotpy",
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "can_claim": True,
        "price": None,
        "message": "Can be claimed directly"
    })


app = app
