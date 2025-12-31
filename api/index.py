import re
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from user_agent import generate_user_agent

app = Flask(__name__)

# ================== SESSION ==================
session = requests.Session()
session.headers.update({
    "User-Agent": generate_user_agent(),
    "Referer": "https://fragment.com/"
})

# ================== CREDITS ==================
API_OWNER = "Paras chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"


# ================== GET FRAGMENT INTERNAL API ==================
def get_fragment_api():
    try:
        r = session.get("https://fragment.com", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                match = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"
        return None
    except:
        return None


# ================== CHECK USERNAME ON FRAGMENT ==================
def check_fragment_username(username, retries=3):
    api_url = get_fragment_api()
    if not api_url:
        return {"error": "Could not fetch Fragment API"}

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        r = session.post(api_url, data=payload, timeout=15)
        data = r.json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fragment_username(username, retries - 1)
        return {"error": "Fragment API request failed"}

    html = data.get("html")
    if not html:
        return {"error": "No data returned from Fragment"}

    soup = BeautifulSoup(html, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return {"error": "Incomplete Fragment response"}

    tag = values[0].get_text(strip=True)
    price = values[1].get_text(strip=True)
    status = values[2].get_text(strip=True)

    return {
        "username": tag,
        "price": price,
        "status": status,
        "on_fragment": True,
        "fragment_url": f"https://fragment.com/username/{username}"
    }


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
def check():
    username = request.args.get("username", "").strip().lower()
    if not username:
        return jsonify({"error": "username required"}), 400

    result = check_fragment_username(username)

    if "error" in result:
        return jsonify({
            "api_owner": API_OWNER,
            "contact": CONTACT,
            "error": result["error"]
        }), 500

    return jsonify({
        "api_owner": API_OWNER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "username": result["username"],
        "status": result["status"],
        "price": result["price"],   # 🔥 REAL PRICE (TON)
        "on_fragment": True,
        "fragment_url": result["fragment_url"]
    })


app = app
