# Telegram Fragment Username Checker API

A FastAPI-based API to check Telegram username availability on both Telegram and Fragment.com marketplace.

## ✨ Features

- ✅ Check if username is taken on Telegram
- ✅ Check if username is listed on Fragment.com
- ✅ Batch processing (up to 50 usernames at once)
- ✅ Username format validation
- ✅ Real-time results
- ✅ CORS enabled for web apps
- ✅ JSON responses
- ✅ Vercel ready deployment

## 🚀 Quick Start

### Single Username Check
```bash
GET /check?username=tobi
