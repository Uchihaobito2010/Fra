import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# ================= SAFE HEADERS =================
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fragment.com/",
    "Accept": "application/json"
}

# ================= CREDITS =================
DEVELOPER = "Paras chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://Aotpy.netlify.app"
CHANNEL = "Obitoapi / @obitostuffs"


# ================= GET FRAGMENT INTERNAL API =================
def frag_api():
    try:
        r = requests.get(
            "https://fragment.com",
            headers=HEADERS,
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                match = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"

        return None
    except:
        return None


# ================= CHECK USERNAME =================
def check_fgusername(username: str, retries=2):
    api_url = frag_api()
    if not api_url:
        return {"error": "Could not get Fragment API"}

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        r = requests.post(
            api_url,
            data=payload,
            headers=HEADERS,
            timeout=15
        )
        response = r.json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {"error": "Fragment API request failed"}

    html = response.get("html")
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
        "price": price,          # REAL FRAGMENT PRICE
        "status": status,
        "available": available,
        "message": (
            "✅ This username might be free or not listed on Fragment"
            if available else ""
        ),
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
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

    result = check_fgusername(username)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
