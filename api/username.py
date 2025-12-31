import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# ---- SESSION ----
session = requests.Session()
session.headers.update({
    "User-Agent": generate_user_agent()
})

# ---- CREDITS ----
DEVELOPER = "Paras Chourasiya"
CONTACT = "https://t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"
CHANNEL = "@obitoapi / @obitostuffs"


def get_fragment_api():
    try:
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if m:
                    return f"https://fragment.com/api?hash={m.group(1)}"
        return None
    except Exception:
        return None


def check_fragment_username(username: str, retries=2):
    api_url = get_fragment_api()
    if not api_url:
        return None

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        r = session.post(api_url, data=payload, timeout=20)
        data = r.json()
    except Exception:
        if retries > 0:
            time.sleep(2)
            return check_fragment_username(username, retries - 1)
        return None

    html_data = data.get("html")
    if not html_data:
        return None

    soup = BeautifulSoup(html_data, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return None

    tag = values[0].get_text(strip=True)
    price = values[1].get_text(strip=True)
    status = values[2].get_text(strip=True)

    available = status.lower() != "sold"

    return {
        "username": tag,
        "price": price,
        "status": status,
        "available": available,
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    }


@app.get("/")
def home():
    return {
        "message": "Fragment Username Check API",
        "usage": "/username?username=telegram",
        "developer": DEVELOPER
    }


@app.get("/username")
def username_check(username: str = Query(..., min_length=1)):
    username = username.strip().lower().replace("@", "")

    result = check_fragment_username(username)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="No data returned from Fragment"
        )

    return result
