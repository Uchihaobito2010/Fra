from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ================== HEADERS ==================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://fragment.com/"
}

# ================== CREDITS ==================
API_OWNER = "Paras chourasiya"
CONTACT = "@Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"


# ================== TON LIVE RATE ==================
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


# ================== TELEGRAM CHECK ==================
def is_telegram_taken(username):
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


# ================== FRAGMENT INTERNAL API ==================
def fragment_lookup(username):
    api_url = f"https://fragment.com/api/username/{username}"
    page_url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(api_url, headers=HEADERS, timeout=15)

        if r.status_code != 200:
            return {"on_fragment": False}

        data = r.json()

        # REAL DATA FROM FRAGMENT
        price_ton = data.get("price")           # <-- REAL PRICE
        for_sale = data.get("for_sale", False)
        sold = data.get("sold", False)

        status = "Available" if for_sale else "Sold" if sold else "Listed"

        return {
            "on_fragment": True,
            "status": status,
            "price_ton": price_ton,
            "url": page_url
        }

    except:
        return {"on_fragment": False}


# ================== ROOT ==================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Telegram Fragment Username Check API",
        "usage": "/check?username=tobi",
        "status": "online",
        "api_owner": API_OWNER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO
    })


# ================== MAIN ENDPOINT ==================
@app.route("/check", methods=["GET"])
def check_username():
    username = request.args.get("username", "").replace("@", "").lower()
    if not username:
        return jsonify({"error": "username required"}), 400

    ton_usd, ton_inr = get_ton_rate()

    # 1️⃣ Telegram taken
    if is_telegram_taken(username):
        return jsonify({
            "api_owner": API_OWNER,
            "contact": CONTACT,
            "username": f"@{username}",
            "status": "Taken",
            "on_fragment": False,
            "can_claim": False,
            "price": None
        })

    # 2️⃣ Fragment check (REAL)
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
            "api_owner": API_OWNER,
            "contact": CONTACT,
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "can_claim": False,
            "price": price,
            "fragment_url": fragment["url"],
            "note": "TON price calculated using live market rate"
        })

    # 3️⃣ Directly claimable
    return jsonify({
        "api_owner": API_OWNER,
        "contact": CONTACT,
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "can_claim": True,
        "price": None,
        "message": "Can be claimed directly"
    })


app = app
