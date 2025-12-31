import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json

# Create FastAPI app
app = FastAPI(
    title="Fragment Username Checker API",
    description="🔍 API to check Telegram username availability on Fragment marketplace",
    version="2.0.0",
    contact={
        "name": "Paras Chourasiya",
        "url": "https://aotpy.netlify.app",
        "email": "paras@aotpy.netlify.app"
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create session with user agent
session = requests.Session()
session.headers.update({
    "User-Agent": generate_user_agent(),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
})

# Developer Information
DEVELOPER = {
    "name": "Paras Chourasiya",
    "telegram": "@aotpy",
    "portfolio": "https://aotpy.netlify.app",
    "github": "https://github.com/aotpy",
    "email": "contact@aotpy.netlify.app"
}

CHANNEL = {
    "name": "TryByte",
    "telegram": "@AnkuCode",
    "description": "Tech & Development Channel"
}

API_INFO = {
    "name": "Fragment Username Checker API",
    "version": "2.0.0",
    "status": "active",
    "uptime": datetime.now().isoformat(),
    "features": [
        "Single username checking",
        "Batch username checking",
        "Real-time Fragment API integration",
        "Detailed availability information",
        "Formatted responses"
    ]
}

def frag_api():
    """Get Fragment API URL dynamically"""
    try:
        r = session.get("https://fragment.com", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                match = re.search(r'hash=([a-fA-F0-9]+)', script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"
        return None
    except Exception as e:
        print(f"Error getting API URL: {e}")
        return None

def format_telegram_link(username: str) -> str:
    """Format Telegram link"""
    return f"https://t.me/{username.lstrip('@')}"

def format_fragment_link(username: str) -> str:
    """Format Fragment marketplace link"""
    return f"https://fragment.com/username/{username.lstrip('@')}"

def check_fgusername(username: str, retries=3):
    """Check username availability on Fragment"""
    api_url = frag_api()
    if not api_url:
        return {
            "error": True,
            "message": f"Could not connect to Fragment API for @{username}",
            "code": "API_CONNECTION_FAILED"
        }

    data = {
        "type": "usernames", 
        "query": username, 
        "method": "searchAuctions"
    }
    
    try:
        response = session.post(api_url, data=data, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {
            "error": True,
            "message": f"API request failed: {str(e)}",
            "code": "API_REQUEST_FAILED"
        }

    html_data = data.get("html")
    if not html_data and retries > 0:
        time.sleep(2)
        return check_fgusername(username, retries - 1)
    elif not html_data:
        return {
            "error": True,
            "message": "No data returned from Fragment",
            "code": "NO_DATA"
        }

    soup = BeautifulSoup(html_data, 'html.parser')
    elements = soup.find_all("div", class_="tm-value")
    
    if len(elements) < 3:
        return {
            "error": True,
            "message": "Insufficient data in Fragment response",
            "code": "INSUFFICIENT_DATA"
        }

    tag = elements[0].get_text(strip=True) or f"@{username}"
    price = elements[1].get_text(strip=True) or "Not Available"
    status = elements[2].get_text(strip=True) or "Unknown"
    
    # Enhanced status detection
    status_lower = status.lower()
    available = "unavailable" in status_lower or "free" in status_lower
    for_sale = "available" in status_lower or "sale" in status_lower
    
    # Generate appropriate messages
    if available:
        message = "🎉 This username appears to be available!"
        emoji = "✅"
        status_type = "available"
    elif for_sale:
        message = "💰 This username is listed for sale on Fragment"
        emoji = "💸"
        status_type = "for_sale"
    else:
        message = "⚠️ This username status is unknown"
        emoji = "❓"
        status_type = "unknown"
    
    # Format price if it's a number
    price_clean = price.replace('TON', '').strip()
    if price_clean.replace('.', '').replace(',', '').isdigit():
        try:
            price_num = float(price_clean.replace(',', ''))
            price_formatted = f"{price_num:,.2f} TON"
        except:
            price_formatted = price
    else:
        price_formatted = price

    return {
        "error": False,
        "data": {
            "username": tag,
            "clean_username": username,
            "price": price_formatted,
            "original_price": price,
            "status": status,
            "status_type": status_type,
            "available": available,
            "for_sale": for_sale,
            "message": f"{emoji} {message}",
            "links": {
                "telegram": format_telegram_link(username),
                "fragment": format_fragment_link(username)
            },
            "checked_at": datetime.now().isoformat()
        },
        "metadata": {
            "source": "fragment.com",
            "cache": False,
            "response_time": None  # Can be populated if timing is added
        }
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with beautiful HTML response"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fragment Username Checker API</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            .logo {{
                font-size: 48px;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 18px;
                opacity: 0.9;
                margin-bottom: 30px;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 25px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .card h2 {{
                margin-top: 0;
                color: #fff;
                border-bottom: 2px solid rgba(255, 255, 255, 0.3);
                padding-bottom: 10px;
            }}
            .endpoint {{
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
                font-family: monospace;
            }}
            .endpoint .method {{
                display: inline-block;
                padding: 5px 15px;
                background: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                margin-right: 10px;
            }}
            .developer-info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }}
            .dev-card {{
                background: rgba(255, 255, 255, 0.15);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
            }}
            .dev-card h3 {{
                margin-top: 0;
            }}
            .link-button {{
                display: inline-block;
                padding: 10px 20px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin: 5px;
                transition: transform 0.3s;
            }}
            .link-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }}
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                font-size: 12px;
                margin: 2px;
            }}
            .api-links {{
                text-align: center;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🔍</div>
                <h1 class="title">Fragment Username Checker API</h1>
                <p class="subtitle">Check Telegram username availability on Fragment marketplace</p>
                <div class="badge">Version {API_INFO['version']}</div>
                <div class="badge">Status: {API_INFO['status'].upper()}</div>
            </div>

            <div class="card">
                <h2>📋 API Endpoints</h2>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/username?username=desired_username</strong>
                    <p>Check single username availability</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/batch?usernames=user1,user2,user3</strong>
                    <p>Check multiple usernames (max 10)</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/health</strong>
                    <p>API health check</p>
                </div>
                <div class="endpoint">
                    <span class="method">GET</span>
                    <strong>/stats</strong>
                    <p>API statistics</p>
                </div>
            </div>

            <div class="api-links">
                <a href="/docs" class="link-button">📚 Interactive API Docs</a>
                <a href="/redoc" class="link-button">📖 Alternative Documentation</a>
                <a href="/health" class="link-button">🩺 Health Check</a>
            </div>

            <div class="developer-info">
                <div class="dev-card">
                    <h3>👨‍💻 Developer</h3>
                    <h4>{DEVELOPER['name']}</h4>
                    <a href="{DEVELOPER['portfolio']}" class="link-button" target="_blank">🌐 Portfolio</a>
                    <a href="https://t.me/{DEVELOPER['telegram'].lstrip('@')}" class="link-button" target="_blank">📱 Telegram</a>
                    <a href="mailto:{DEVELOPER['email']}" class="link-button">✉️ Email</a>
                </div>

                <div class="dev-card">
                    <h3>📢 Channel</h3>
                    <h4>{CHANNEL['name']}</h4>
                    <p>{CHANNEL['description']}</p>
                    <a href="https://t.me/{CHANNEL['telegram'].lstrip('@')}" class="link-button" target="_blank">📢 Join Channel</a>
                </div>

                <div class="dev-card">
                    <h3>⚡ Features</h3>
                    <p>• Real-time Fragment API integration</p>
                    <p>• Batch username checking</p>
                    <p>• Detailed availability status</p>
                    <p>• Formatted responses</p>
                    <p>• CORS enabled</p>
                </div>
            </div>

            <div style="text-align: center; margin-top: 40px; opacity: 0.8; font-size: 14px;">
                <p>Made with ❤️ by {DEVELOPER['name']} | {CHANNEL['name']}</p>
                <p>API Uptime: {API_INFO['uptime']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test Fragment API connection
        api_url = frag_api()
        if api_url:
            api_status = "healthy"
            fragment_accessible = True
        else:
            api_status = "unhealthy"
            fragment_accessible = False
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "operational",
                "fragment_api": api_status,
                "database": "none"
            },
            "uptime": API_INFO['uptime'],
            "version": API_INFO['version'],
            "response_time": None
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stats")
async def get_stats():
    """Get API statistics"""
    return {
        "api": API_INFO,
        "developer": DEVELOPER,
        "channel": CHANNEL,
        "timestamp": datetime.now().isoformat(),
        "usage": {
            "rate_limit": "Unlimited (for now)",
            "batch_limit": 10,
            "features": API_INFO['features']
        }
    }

@app.get("/username")
async def check_username(
    username: str = Query(..., min_length=1, description="Telegram username to check (without @)"),
    format: str = Query("json", description="Response format: json or html")
):
    """
    Check if a Telegram username is available on Fragment marketplace
    
    - **username**: The Telegram username (without @ symbol)
    - **format**: Response format (json or html)
    """
    start_time = time.time()
    username = username.strip().lower().lstrip('@')
    
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    if not username.replace('_', '').isalnum():
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores")
    
    if len(username) < 5:
        raise HTTPException(status_code=400, detail="Username must be at least 5 characters")
    
    result = check_fgusername(username)
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)
    
    if result.get("error"):
        error_result = {
            "success": False,
            "error": result.get("message", "Unknown error"),
            "code": result.get("code", "UNKNOWN_ERROR"),
            "username": f"@{username}",
            "timestamp": datetime.now().isoformat(),
            "developer": DEVELOPER,
            "channel": CHANNEL,
            "response_time": f"{response_time}ms"
        }
        
        if format.lower() == "html":
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Error - {username}</title></head>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1>❌ Error Checking @{username}</h1>
                <p><strong>Error:</strong> {error_result['error']}</p>
                <p><strong>Code:</strong> {error_result['code']}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>Developer: {DEVELOPER['name']} | Contact: <a href="https://t.me/{DEVELOPER['telegram'].lstrip('@')}">Telegram</a></p>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        raise HTTPException(status_code=500, detail=error_result)
    
    # Add response time to result
    if "metadata" in result:
        result["metadata"]["response_time"] = f"{response_time}ms"
    
    # Add credits
    result["credits"] = {
        "developer": DEVELOPER,
        "channel": CHANNEL,
        "powered_by": "Fragment API",
        "api_version": API_INFO['version']
    }
    
    if format.lower() == "html":
        data = result["data"]
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Result - {data['username']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }}
                .result {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .available {{ color: green; }}
                .unavailable {{ color: red; }}
                .button {{ display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🔍 Username Check Result</h1>
            <div class="result">
                <h2>{data['username']}</h2>
                <p><strong>Status:</strong> <span class="{data['status_type']}">{data['status']}</span></p>
                <p><strong>Price:</strong> {data['price']}</p>
                <p><strong>Availability:</strong> {"✅ Available" if data['available'] else "❌ Not Available"}</p>
                <p><strong>Message:</strong> {data['message']}</p>
                <p><strong>Checked at:</strong> {data['checked_at']}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <a href="{data['links']['telegram']}" class="button" target="_blank">Open in Telegram</a>
                <a href="{data['links']['fragment']}" class="button" target="_blank">View on Fragment</a>
            </div>
            
            <div style="border-top: 1px solid #ddd; padding-top: 20px; font-size: 0.9em; color: #666;">
                <p>Response time: {response_time}ms</p>
                <p>Developer: {DEVELOPER['name']} (<a href="https://t.me/{DEVELOPER['telegram'].lstrip('@')}">@{DEVELOPER['telegram'].lstrip('@')}</a>)</p>
                <p>Channel: {CHANNEL['name']} (<a href="https://t.me/{CHANNEL['telegram'].lstrip('@')}">@{CHANNEL['telegram'].lstrip('@')}</a>)</p>
                <p>API Version: {API_INFO['version']} | Powered by Fragment.com</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    return result

@app.get("/batch")
async def batch_check(
    usernames: str = Query(..., description="Comma-separated list of usernames (max 10)"),
    format: str = Query("json", description="Response format: json or html")
):
    """
    Check multiple usernames at once
    
    - **usernames**: Comma-separated list of usernames
    - **format**: Response format (json or html)
    """
    start_time = time.time()
    username_list = [u.strip().lower().lstrip('@') for u in usernames.split(',')]
    username_list = [u for u in username_list if u]
    
    if not username_list:
        raise HTTPException(status_code=400, detail="No valid usernames provided")
    
    if len(username_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 usernames per request")
    
    results = []
    for username in username_list:
        result = check_fgusername(username)
        results.append({
            "username": f"@{username}",
            "result": result
        })
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    if format.lower() == "html":
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Batch Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .result {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .success {{ border-left: 5px solid green; }}
                .error {{ border-left: 5px solid red; }}
                .summary {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>📊 Batch Username Check Results</h1>
            <div class="summary">
                <p><strong>Total Checked:</strong> {len(results)} usernames</p>
                <p><strong>Response Time:</strong> {response_time}ms</p>
                <p><strong>Completed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for item in results:
            if item["result"].get("error"):
                html_content += f"""
                <div class="result error">
                    <h3>❌ {item['username']}</h3>
                    <p><strong>Error:</strong> {item['result'].get('message', 'Unknown error')}</p>
                </div>
                """
            else:
                data = item["result"]["data"]
                html_content += f"""
                <div class="result success">
                    <h3>{data['username']}</h3>
                    <p><strong>Status:</strong> {data['status']}</p>
                    <p><strong>Price:</strong> {data['price']}</p>
                    <p><strong>Available:</strong> {"✅ Yes" if data['available'] else "❌ No"}</p>
                    <p><a href="{data['links']['telegram']}" target="_blank">Telegram</a> | 
                       <a href="{data['links']['fragment']}" target="_blank">Fragment</a></p>
                </div>
                """
        
        html_content += f"""
            <div style="border-top: 1px solid #ddd; padding-top: 20px; color: #666;">
                <p>Developer: {DEVELOPER['name']} | Telegram: <a href="https://t.me/{DEVELOPER['telegram'].lstrip('@')}">@{DEVELOPER['telegram'].lstrip('@')}</a></p>
                <p>Channel: {CHANNEL['name']} | Portfolio: <a href="{DEVELOPER['portfolio']}" target="_blank">{DEVELOPER['portfolio']}</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    return {
        "success": True,
        "batch_results": results,
        "summary": {
            "total_checked": len(results),
            "successful": len([r for r in results if not r["result"].get("error")]),
            "failed": len([r for r in results if r["result"].get("error")]),
            "response_time": f"{response_time}ms",
            "timestamp": datetime.now().isoformat()
        },
        "credits": {
            "developer": DEVELOPER,
            "channel": CHANNEL,
            "api_info": API_INFO
        }
    }

@app.get("/credits")
async def get_credits():
    """Get detailed credit information"""
    return {
        "api": API_INFO,
        "developer": DEVELOPER,
        "channel": CHANNEL,
        "attribution": f"Powered by {DEVELOPER['name']} | Channel: {CHANNEL['name']}",
        "links": {
            "developer_portfolio": DEVELOPER['portfolio'],
            "developer_telegram": f"https://t.me/{DEVELOPER['telegram'].lstrip('@')}",
            "channel_telegram": f"https://t.me/{CHANNEL['telegram'].lstrip('@')}",
            "github_repo": "https://github.com/aotpy/fragment-api"
        },
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom error handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "developer": DEVELOPER,
            "channel": CHANNEL
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "type": exc.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
            "developer": DEVELOPER,
            "channel": CHANNEL
        }
    )
