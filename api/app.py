"""
Telegram Username Availability Checker API
Author: Paras Chourasiya
Contact: t.me/Aotpy
Portfolio: https://aotpy.vercel.app
"""

from http.server import BaseHTTPRequestHandler
import json
import requests
import re
import time
import urllib.parse
from datetime import datetime

API_OWNER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"
CHANNEL = "@obitoapi / @obitostuffs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse the path
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            # Set CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            if path == '/':
                response = self.home_endpoint()
                self.send_json_response(200, response)
                
            elif path == '/check':
                response = self.check_endpoint(parsed_path.query)
                self.send_json_response(200, response)
                
            elif path == '/batch':
                response = {"error": "Use POST method for batch endpoint", "example": {"usernames": ["user1", "user2"]}}
                self.send_json_response(400, response)
                
            elif path == '/health':
                response = self.health_endpoint()
                self.send_json_response(200, response)
                
            elif path == '/status':
                response = self.status_endpoint()
                self.send_json_response(200, response)
                
            elif path == '/validate':
                response = self.validate_endpoint(parsed_path.query)
                self.send_json_response(200, response)
                
            else:
                response = {
                    "error": "Endpoint not found",
                    "available_endpoints": [
                        "/",
                        "/check?username=example",
                        "/batch (POST)",
                        "/health",
                        "/status",
                        "/validate?username=example"
                    ]
                }
                self.send_json_response(404, response)
                
        except Exception as e:
            error_response = {
                "error": "Internal server error",
                "message": str(e),
                "contact": CONTACT
            }
            self.send_json_response(500, error_response)
    
    def do_POST(self):
        """Handle POST requests for batch checking"""
        try:
            if self.path == '/batch':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    usernames = data.get('usernames', [])
                    
                    if not usernames or not isinstance(usernames, list):
                        response = {
                            "error": "Please provide 'usernames' array in JSON body",
                            "example": {"usernames": ["user1", "user2", "user3"]}
                        }
                        self.send_json_response(400, response)
                        return
                    
                    if len(usernames) > 50:
                        response = {"error": "Maximum 50 usernames allowed per batch"}
                        self.send_json_response(400, response)
                        return
                    
                    results = []
                    for username in usernames:
                        result = self.check_single_username(username)
                        results.append(result)
                    
                    response = {
                        "results": results,
                        "total": len(results),
                        "batch_checked": True,
                        "checked_at": self.get_timestamp(),
                        "api_owner": API_OWNER
                    }
                    self.send_json_response(200, response)
                    
                except json.JSONDecodeError:
                    response = {"error": "Invalid JSON format"}
                    self.send_json_response(400, response)
            else:
                response = {"error": "POST method only allowed for /batch endpoint"}
                self.send_json_response(405, response)
                
        except Exception as e:
            error_response = {
                "error": "Internal server error",
                "message": str(e)
            }
            self.send_json_response(500, error_response)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    # ========== ENDPOINT HANDLERS ==========
    
    def home_endpoint(self):
        """Homepage with API documentation"""
        return {
            "api": "Telegram Fragment Username Checker API",
            "version": "2.0",
            "author": API_OWNER,
            "contact": CONTACT,
            "portfolio": PORTFOLIO,
            "channel": CHANNEL,
            "description": "Check Telegram username availability on Telegram and Fragment.com marketplace",
            "endpoints": {
                "GET /": "API documentation (this page)",
                "GET /check?username=xxx": "Check single username availability",
                "POST /batch": "Check multiple usernames (send JSON: {\"usernames\": [\"user1\", \"user2\"]})",
                "GET /health": "API health check",
                "GET /status": "API status and features",
                "GET /validate?username=xxx": "Validate username format"
            },
            "examples": {
                "single_check": "https://your-api.vercel.app/check?username=tobi",
                "batch_check_curl": "curl -X POST https://your-api.vercel.app/batch -H 'Content-Type: application/json' -d '{\"usernames\":[\"tobi\",\"naruto\"]}'",
                "validate": "https://your-api.vercel.app/validate?username=test123"
            },
            "note": "Username should be without @ symbol",
            "timestamp": self.get_timestamp()
        }
    
    def check_endpoint(self, query_string):
        """Check single username endpoint"""
        params = urllib.parse.parse_qs(query_string)
        username = params.get('username', [''])[0].replace('@', '').strip().lower()
        
        if not username:
            return {
                "error": "Username parameter is required",
                "example": "/check?username=example",
                "note": "Do not include @ symbol"
            }
        
        return self.check_single_username(username)
    
    def validate_endpoint(self, query_string):
        """Validate username format"""
        params = urllib.parse.parse_qs(query_string)
        username = params.get('username', [''])[0].replace('@', '').strip()
        
        if not username:
            return {
                "error": "Username parameter is required",
                "example": "/validate?username=example"
            }
        
        is_valid = self.validate_username_format(username)
        
        return {
            "username": f"@{username}",
            "valid": is_valid,
            "validation_rules": {
                "min_length": 5,
                "max_length": 32,
                "allowed_characters": "a-z, A-Z, 0-9, underscore (_)",
                "no_spaces": True,
                "no_special_chars": True,
                "cannot_start_with_number": False,
                "cannot_end_with_underscore": False
            },
            "message": "Valid Telegram username format" if is_valid else "Invalid Telegram username format"
        }
    
    def health_endpoint(self):
        """Health check endpoint"""
        # Test Telegram
        telegram_test = self.test_telegram()
        fragment_test = self.test_fragment()
        
        all_ok = telegram_test and fragment_test
        
        return {
            "status": "healthy" if all_ok else "partial",
            "services": {
                "telegram": "operational" if telegram_test else "unavailable",
                "fragment": "operational" if fragment_test else "unavailable"
            },
            "timestamp": self.get_timestamp(),
            "response_time": "N/A",
            "api_version": "2.0"
        }
    
    def status_endpoint(self):
        """API status endpoint"""
        return {
            "api": "Telegram Fragment Username Checker",
            "status": "operational",
            "version": "2.0",
            "features": [
                "Real-time Telegram username check",
                "Fragment.com marketplace integration",
                "Batch processing (up to 50 usernames)",
                "Username format validation",
                "CORS enabled",
                "JSON responses"
            ],
            "rate_limits": "None currently applied",
            "uptime": "100% (since deployment)",
            "maintenance": "No scheduled maintenance",
            "support": CONTACT,
            "last_updated": "2024-12-30"
        }
    
    # ========== CORE FUNCTIONS ==========
    
    def check_single_username(self, username):
        """Core function to check a single username"""
        # Validate format first
        if not self.validate_username_format(username):
            return {
                "username": f"@{username}",
                "status": "Invalid Format",
                "valid": False,
                "message": "Invalid Telegram username format",
                "telegram_taken": False,
                "on_fragment": False,
                "can_claim": False,
                "api_owner": API_OWNER,
                "checked_at": self.get_timestamp()
            }
        
        # Check Telegram
        telegram_taken = self.check_telegram(username)
        
        if telegram_taken is None:
            # Telegram check failed
            return {
                "username": f"@{username}",
                "status": "Telegram Check Failed",
                "valid": True,
                "message": "Unable to check Telegram status",
                "telegram_taken": None,
                "on_fragment": False,
                "can_claim": None,
                "api_owner": API_OWNER,
                "checked_at": self.get_timestamp()
            }
        
        if telegram_taken:
            # Username is taken on Telegram
            return {
                "username": f"@{username}",
                "status": "Taken on Telegram",
                "valid": True,
                "message": "Username is already in use on Telegram",
                "telegram_taken": True,
                "on_fragment": False,
                "can_claim": False,
                "api_owner": API_OWNER,
                "checked_at": self.get_timestamp()
            }
        
        # Check Fragment
        fragment_data = self.check_fragment(username)
        
        if fragment_data.get("on_fragment"):
            # On Fragment marketplace
            status_messages = {
                "Sold": "This username was sold on Fragment",
                "Available": "Available for purchase on Fragment",
                "Auction": "Available for auction on Fragment",
                "Reserved": "Reserved username on Fragment"
            }
            
            status = fragment_data.get("status", "Listed")
            message = status_messages.get(status, "Listed on Fragment marketplace")
            
            return {
                "username": f"@{username}",
                "status": status,
                "valid": True,
                "message": message,
                "telegram_taken": False,
                "on_fragment": True,
                "price_ton": fragment_data.get("price"),
                "fragment_url": fragment_data.get("url"),
                "can_claim": False,
                "api_owner": API_OWNER,
                "contact": CONTACT,
                "checked_at": self.get_timestamp()
            }
        
        # Available for claiming
        return {
            "username": f"@{username}",
            "status": "Available",
            "valid": True,
            "message": "Username is available and can be claimed on Telegram",
            "telegram_taken": False,
            "on_fragment": False,
            "can_claim": True,
            "api_owner": API_OWNER,
            "contact": CONTACT,
            "checked_at": self.get_timestamp()
        }
    
    def validate_username_format(self, username):
        """Validate Telegram username format"""
        if not username or len(username) < 5 or len(username) > 32:
            return False
        
        # Telegram username pattern: letters, numbers, underscores
        pattern = r'^[a-zA-Z0-9_]+$'
        if not re.match(pattern, username):
            return False
        
        # Additional Telegram rules
        if username.endswith('_') or '__' in username:
            return False
        
        return True
    
    def check_telegram(self, username):
        """Check if username is taken on Telegram"""
        try:
            url = f"https://t.me/{username}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            # If page contains "If you have Telegram" - it's available
            if "If you have <strong>Telegram</strong>, you can contact" in response.text:
                return False
            
            # If it contains Telegram page elements - it's taken
            if "tgme_page" in response.text or "tgme_widget_message" in response.text:
                return True
            
            return False
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException:
            return None
    
    def check_fragment(self, username):
        """Check Fragment.com for username"""
        url = f"https://fragment.com/username/{username}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 404:
                return {"on_fragment": False}
            
            html_content = response.text.lower()
            
            # Check for sold
            sold_indicators = [
                "this username was sold",
                "sold for",
                "final price",
                "this lot is sold",
                "auction ended"
            ]
            
            for indicator in sold_indicators:
                if indicator in html_content:
                    price_match = re.search(r'([\d,]+)\s*ton', html_content)
                    price = price_match.group(1).replace(',', '') if price_match else None
                    return {
                        "on_fragment": True,
                        "status": "Sold",
                        "price": price,
                        "url": url
                    }
            
            # Check for available/auction
            available_indicators = [
                "buy username",
                "place a bid",
                "current bid",
                "starting price",
                "auction ends"
            ]
            
            for indicator in available_indicators:
                if indicator in html_content:
                    price_match = re.search(r'([\d,]+)\s*ton', html_content)
                    price = price_match.group(1).replace(',', '') if price_match else None
                    
                    status = "Auction" if "auction" in indicator else "Available"
                    
                    return {
                        "on_fragment": True,
                        "status": status,
                        "price": price,
                        "url": url
                    }
            
            # Check for reserved
            if "reserved" in html_content or "premium" in html_content:
                return {
                    "on_fragment": True,
                    "status": "Reserved",
                    "price": None,
                    "url": url
                }
            
            # Not on fragment
            return {"on_fragment": False}
            
        except requests.exceptions.RequestException:
            return {"on_fragment": False}
    
    def test_telegram(self):
        """Test Telegram connectivity"""
        try:
            response = requests.get("https://t.me/telegram", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_fragment(self):
        """Test Fragment connectivity"""
        try:
            response = requests.get("https://fragment.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_timestamp(self):
        """Get current timestamp"""
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
