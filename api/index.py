import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# ================== HEADERS ==================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://fragment.com/",
    "Accept": "application/json"
}

# ================== CREDITS ==================
DEVELOPER = "Paras chourasiya"
CONTACT = "https://t.me/Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"
CHANNEL = "@obitostuffs / @obitoapi"


# ================== GET FRAGMENT API HASH ==================
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


# ================== CHECK USERNAME ==================
def check_fragment_username(username: str, retries=3):
    api_url = get_fragment_api()
    if not api_url:
        return {"error": "Failed to fetch Fragment API hash"}

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

    available = status.lower() == "unavailable"

    return {
        "username": tag,
        "price": price,
        "status": status,
        "available": available
    }


# ================== ROOT ==================
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


# ================== MAIN ENDPOINT ==================
@app.get("/username")
async def check_username(username: str = Query(..., min_length=1)):
    username = username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    result = check_fragment_username(username)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL,
        **result
    }
