import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# ================= HEADERS =================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://fragment.com/",
    "Accept": "application/json"
}

# ================= CREDITS =================
DEVELOPER = "Paras chourasiya"
CONTACT = "https://t.me/Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"
CHANNEL = "Obito | Tobi Tools"


# ================= GET FRAGMENT API =================
def get_fragment_api():
    try:
        r = requests.get("https://fragment.com", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if m:
                    return f"https://fragment.com/api?hash={m.group(1)}"

        return None
    except:
        return None


# ================= FRAGMENT CHECK =================
def check_fragment_username(username: str, retries=2):
    api_url = get_fragment_api()

    # Fragment unreachable → still safe response
    if not api_url:
        return {
            "username": f"@{username}",
            "price": None,
            "status": "Not listed on Fragment",
            "available": True
        }

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        r = requests.post(api_url, data=payload, headers=HEADERS, timeout=20)
        data = r.json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fragment_username(username, retries - 1)
        return {
            "username": f"@{username}",
            "price": None,
            "status": "Not listed on Fragment",
            "available": True
        }

    html = data.get("html")

    # ✅ CORE FIX — empty html is NOT an error
    if not html:
        return {
            "username": f"@{username}",
            "price": None,
            "status": "Not listed on Fragment",
            "available": True
        }

    soup = BeautifulSoup(html, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return {
            "username": f"@{username}",
            "price": None,
            "status": "Not listed on Fragment",
            "available": True
        }

    tag = values[0].get_text(strip=True)
    price = values[1].get_text(strip=True)
    status = values[2].get_text(strip=True)

    available = status.lower() == "unavailable"

    return {
        "username": tag,
        "price": price,
        "status": status,
        "available": available
    }
# ================= ROOT =================
@app.get("/")
async def root():
    return {
        "api": "Telegram Fragment Username Checker API",
        "usage": "/username?username=tobi",
        "status": "online",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    }


# ================= MAIN ENDPOINT =================
@app.get("/username")
async def check_username(username: str = Query(..., min_length=1)):
    username = username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    result = check_fragment_username(username)

    return {
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL,
        **result
    }
