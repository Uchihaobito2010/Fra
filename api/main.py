import re
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Telegram Username Checker API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ---- FUNCTION 1: Check if Telegram username is taken ----
def is_telegram_taken(username: str) -> bool:
    """Check if username is already taken on Telegram"""
    try:
        url = f"https://t.me/{username}"
        r = session.get(url, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except Exception:
        return False

# ---- FUNCTION 2: Get price from Fragment API ----
def get_fragment_api():
    """Get Fragment API URL with hash"""
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

def get_fragment_price(username: str):
    """Get price from Fragment API"""
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

    # Extract numeric price if available
    price_ton = None
    if price and "ton" in price.lower():
        m = re.search(r'([\d,]+\.?\d*)\s*ton', price, re.IGNORECASE)
        if m:
            price_ton = m.group(1).replace(",", "")

    return {
        "username": tag,
        "price": price,
        "price_ton": price_ton,
        "status": status,
        "available": status.lower() != "sold"
    }

# ---- FUNCTION 3: Fragment lookup with scraping ----
def fragment_lookup(username: str):
    """Check if username is on Fragment marketplace"""
    url = f"https://fragment.com/username/{username}"
    
    try:  
        r = session.get(url, timeout=15)  
        if r.status_code != 200:  
            return {"on_fragment": False}  

        html = r.text.lower()  

        # ---------- STRICT SOLD DETECTION ----------  
        sold_signals = [  
            "this username was sold",  
            "sold for",  
            "final price"  
        ]  

        if any(sig in html for sig in sold_signals):  
            return {  
                "on_fragment": True,  
                "status": "Sold",  
                "url": url  
            }  

        # ---------- PRICE EXTRACTION ----------  
        price_ton = None
        m = re.search(r'([\d,]{3,})\s*ton', html)  
        if m:  
            price_ton = m.group(1).replace(",", "")  

        # ---------- LISTED ON FRAGMENT ----------  
        fragment_signals = [  
            "buy username",  
            "place a bid",  
            "fragment marketplace"  
        ]  

        if any(sig in html for sig in fragment_signals):  
            return {  
                "on_fragment": True,  
                "status": "Available",  
                "price_ton": price_ton,  
                "url": url  
            }  

        # ---------- NOT ON FRAGMENT ----------  
        return {"on_fragment": False}  

    except Exception:  
        return {"on_fragment": False}

# ---- MAIN CHECK FUNCTION ----
def check_username_full(username: str):
    """Complete username check with all features"""
    username = username.strip().lower().replace("@", "")
    
    # 1. Check if taken on Telegram
    telegram_taken = is_telegram_taken(username)
    
    # 2. Get price from Fragment API
    fragment_price_data = get_fragment_price(username)
    
    # 3. Check Fragment marketplace
    fragment_market_data = fragment_lookup(username)
    
    # Prepare base response
    response = {
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL,
        "username": f"@{username}",
        "telegram_taken": telegram_taken,
        "on_fragment": fragment_market_data.get("on_fragment", False),
    }
    
    # Add price information from Fragment API if available
    if fragment_price_data:
        response.update({
            "fragment_status": fragment_price_data.get("status"),
            "price_display": fragment_price_data.get("price"),
            "price_ton": fragment_price_data.get("price_ton"),
            "available_on_fragment": fragment_price_data.get("available", False)
        })
    else:
        # Fallback to market data
        response.update({
            "fragment_status": fragment_market_data.get("status"),
            "price_ton": fragment_market_data.get("price_ton"),
            "available_on_fragment": fragment_market_data.get("status") == "Available"
        })
    
    # Determine overall status and claimability
    if telegram_taken:
        response["status"] = "Taken"
        response["can_claim"] = False
        response["message"] = "Username already taken on Telegram"
    elif response.get("on_fragment"):
        if response.get("fragment_status") == "Available":
            response["status"] = "On Fragment"
            response["can_claim"] = False
            response["message"] = "Buy from Fragment marketplace"
        else:
            response["status"] = "Sold on Fragment"
            response["can_claim"] = False
            response["message"] = "Previously sold on Fragment"
    else:
        response["status"] = "Available"
        response["can_claim"] = True
        response["message"] = "Can be claimed directly"
    
    # Add Fragment URL if available
    if fragment_market_data.get("url"):
        response["fragment_url"] = fragment_market_data.get("url")
    
    return response

# ---- API ENDPOINTS ----
@app.get("/")
def home():
    return {
        "api": "Telegram Username Checker",
        "version": "2.0",
        "description": "Check Telegram username availability and Fragment prices",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "endpoints": {
            "/": "This info page",
            "/check?username={username}": "Full username check",
            "/price?username={username}": "Get Fragment price only"
        },
        "example": "https://your-api.vercel.app/check?username=telegram"
    }

@app.get("/check")
def check_username(username: str = Query(..., min_length=1, description="Telegram username without @ symbol")):
    """Complete username check endpoint"""
    if len(username) > 32:
        raise HTTPException(status_code=400, detail="Username too long (max 32 characters)")
    
    result = check_username_full(username)
    return result

@app.get("/price")
def get_price(username: str = Query(..., min_length=1, description="Telegram username without @ symbol")):
    """Get Fragment price only"""
    username = username.strip().lower().replace("@", "")
    
    price_data = get_fragment_price(username)
    if not price_data:
        raise HTTPException(
            status_code=404,
            detail="No price data found on Fragment"
        )
    
    # Add credits to response
    price_data.update({
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    })
    
    return price_data

@app.get("/status")
def api_status():
    """API status check"""
    import time
    return {
        "status": "online",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "service": "Telegram Username Checker"
    }

# Required for Vercel
app = app
