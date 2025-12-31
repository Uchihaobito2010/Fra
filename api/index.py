from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import requests
import re

# ================== CREDITS ==================
API_OWNER = "Tobi (Obito Vision)"
BRAND = "Tobi Tools"
CONTACT = "@Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"

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
            timeout=6
        )
        data = r.json().get("the-open-network", {})
        return data.get("usd"), data.get("inr")
    except:
        return None, None


# ================== FRAGMENT LOOKUP ==================
def fragment_lookup(username):
    api_url = "https://fragment.com/api"

    def call_fragment(method):
        payload = {
            "type": "usernames",
            "query": username,
            "method": method
        }
        try:
            r = requests.post(api_url, data=payload, headers=HEADERS, timeout=8)
            if r.status_code != 200:
                return None
            return r.json().get("html")
        except:
            return None

    # Auction
    html = call_fragment("searchAuctions")

    # Direct / premium
    if not html:
        html = call_fragment("searchUsernames")

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

    # Fallback: page exists
    try:
        page = requests.get(
            f"https://fragment.com/username/{username}",
            headers=HEADERS,
            timeout=6
        )
        if page.status_code == 200:
            return {
                "on_fragment": True,
                "status": "Available (Premium)",
                "price_ton": None,
                "fragment_url": f"https://fragment.com/username/{username}"
            }
    except:
        pass

    return {
        "on_fragment": False,
        "status": "Not listed",
        "price_ton": None
    }


# ================== HANDLER ==================
class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # ---------- /api ----------
        if path == "/api":
            self.respond(200, {
                "api": "Telegram Fragment Username API",
                "brand": BRAND,
                "owner": API_OWNER,
                "contact": CONTACT,
                "portfolio": PORTFOLIO,
                "status": "online"
            })
            return

        # ---------- /api/fragment/check ----------
        if path == "/api/fragment/check":
            username = query.get("username", [None])[0]

            if not username or not username.isalnum():
                self.respond(400, {"error": "Invalid username"})
                return

            username = username.lower()

            ton_usd, ton_inr = get_ton_rate()
            frag = fragment_lookup(username)

            price = None
            if frag.get("price_ton") and ton_usd:
                price = {
                    "ton": frag["price_ton"],
                    "usd": round(frag["price_ton"] * ton_usd, 2),
                    "inr": round(frag["price_ton"] * ton_inr, 2) if ton_inr else None
                }

            self.respond(200, {
                "brand": BRAND,
                "owner": API_OWNER,
                "contact": CONTACT,
                "username": f"@{username}",
                "on_fragment": frag.get("on_fragment"),
                "status": frag.get("status"),
                "price": price,
                "fragment_url": frag.get("fragment_url")
            })
            return

        # ---------- 404 ----------
        self.respond(404, {"error": "Not Found"})

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
