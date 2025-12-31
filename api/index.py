import re
import requests
from fastapi import FastAPI, Query

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

def is_telegram_taken(username: str) -> bool:
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


def fragment_lookup(username: str):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"on_fragment": False}

        html = r.text.lower()

        if any(x in html for x in ["this username was sold", "sold for", "final price"]):
            return {
                "on_fragment": True,
                "status": "Sold",
                "price": None,
                "url": url
            }

        price = None
        m = re.search(r'([\d,]+)\s*ton', html)
        if m:
            price = m.group(1).replace(",", "")

        if any(x in html for x in ["buy username", "place a bid", "fragment marketplace"]):
            return {
                "on_fragment": True,
                "status": "Available",
                "price": price,
                "url": url
            }

        return {"on_fragment": False}

    except:
        return {"on_fragment": False}


@app.get("/")
def home():
    return {
        "api_owner": "Paras Chourasiya",
        "contact": "https://t.me/Aotpy",
        "portfolio": "https://aotpy.vercel.app",
        "usage": "/check?username=tobi",
        "status": "online"
    }


@app.get("/check")
def check(username: str = Query(...)):
    username = username.replace("@", "").lower()

    if is_telegram_taken(username):
        return {
            "username": f"@{username}",
            "status": "Taken",
            "price_ton": "Unknown",
            "on_fragment": False,
            "can_claim": False
        }

    fragment = fragment_lookup(username)

    if fragment.get("on_fragment"):
        return {
            "username": f"@{username}",
            "status": fragment.get("status"),
            "price_ton": fragment.get("price") or "Unknown",
            "on_fragment": True,
            "can_claim": False,
            "fragment_url": fragment.get("url")
        }

    return {
        "username": f"@{username}",
        "status": "Available",
        "price_ton": "Unknown",
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly"
    }
