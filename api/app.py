from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

# ================== CREDITS ==================
API_OWNER = "Tobi (Obito Vision)"
BRAND = "Tobi Tools"
CONTACT = "@Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"

# ================== HEADERS ==================
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://fragment.com/"
}

# ================== TON RATE ==================
def get_ton_rate():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "the-open-network",
                "vs_currencies": "usd,inr"
            },
            timeout=8
        )
        data = r.json().get("the-open-network", {})
        return data.get("usd"), data.get("inr")
    except:
        return None, None


# ================== FRAGMENT LOOKUP (FINAL) ==================
def fragment_lookup(username):
    api_url = "https://fragment.com/api"

    def call_fragment(method):
        payload = {
            "type": "usernames",
            "query": username,
            "method": method
        }
        try:
            r = requests.post(api_url, data=payload, headers=HEADERS, timeout=10)
            if r.status_code != 200:
                return None
            return r.json().get("html")
        except:
            return None

    # 1️⃣ Auction
    html = call_fragment("searchAuctions")

    # 2️⃣ Direct / premium
    if not html:
        html = call_fragment("searchUsernames")

    # 3️⃣ Parse if HTML exists
    if html:
        lower = html.lower()

        price = None
        m = re.search(r'([\d,]+)\s*ton', lower)
        if m:
            price = float(m.group(1).replace(",", ""))

        status = "Sold" if "sold" in lower else "Available"

        return {
            "on_fragment": True,
            "status": status,
            "price_ton": price,
            "fragment_url": f"https://fragment.com/username/{username}"
        }

    # 4️⃣ FINAL FALLBACK — check Fragment page existence
    try:
        page = requests.get(
            f"https://fragment.com/username/{username}",
            headers=HEADERS,
            timeout=8
        )
        if page.status_code == 200:
            # Page exists → premium / hidden listing
            return {
                "on_fragment": True,
                "status": "Available (Premium)",
                "price_ton": None,
                "fragment_url": f"https://fragment.com/username/{username}"
            }
    except:
        pass

    # 5️⃣ Truly not listed
    return {
        "on_fragment": False,
        "status": "Not listed",
        "price_ton": None
    }

# ================== API INFO ==================
@app.route("/api")
def api_info():
    return jsonify({
        "api": "Telegram Fragment Username API",
        "brand": BRAND,
        "owner": API_OWNER,
        "usage": "/api/fragment/check?username=tobi",
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "status": "online"
    })


# ================== MAIN CHECK ==================
@app.route("/api/fragment/check")
def check_fragment():
    username = request.args.get("username", "").strip().lower()

    if not username or not username.isalnum():
        return jsonify({"error": "Invalid username format"}), 400

    ton_usd, ton_inr = get_ton_rate()
    frag = fragment_lookup(username)

    price = None
    if frag.get("price_ton") and ton_usd:
        price = {
            "ton": frag["price_ton"],
            "usd": round(frag["price_ton"] * ton_usd, 2),
            "inr": round(frag["price_ton"] * ton_inr, 2) if ton_inr else None
        }

    return jsonify({
        "brand": BRAND,
        "owner": API_OWNER,
        "contact": CONTACT,
        "username": f"@{username}",
        "on_fragment": frag.get("on_fragment"),
        "status": frag.get("status"),
        "price": price,
        "fragment_url": frag.get("fragment_url")
    })


app = app
