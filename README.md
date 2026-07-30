# 🚀 SkyMoviesHD Universal GDFlix Scraper — Pure REST API Backend

**Render / Heroku / Railway / Docker Deployable Pure Backend (FastAPI)**  
*Universal GDFlix Cloud Download Link Extractor for SkyMoviesHD.ceo*

---

## ✨ Why Pure Backend?
- **Zero Frontend Overhead**: No HTML/UI files — lightweight, fast JSON responses.
- **Ready for any Frontend/Client**: Integrate with Android apps, Telegram bots, Discord bots, Web dashboards, or curl scripts.
- **Interactive Swagger Documentation**: Automatically hosts OpenAPI UI at `/docs` and Redoc at `/redoc`.

---

## ⚡ Core Endpoints Overview

### 1. Root Health Check (`GET /`)
Returns backend service status and API map:
```json
{
  "service": "SkyMoviesHD Universal GDFlix Scraper API",
  "version": "2.0.0",
  "status": "online",
  "swagger_documentation": "/docs",
  "endpoints": { ... }
}
```

### 2. Universal GDFlix Extractor (`GET /api/extract_gdflix?url=...`)
**"khi par bhi sare links me se gdflix ki link ko nikal kar dega"**  
Pass ANY URL to automatically resolve and extract GDFlix links:
- Direct GDFlix URL (`https://gdflix.dev/file/...`)
- HowBlogs / Tpead Shortener (`https://howblogs.xyz/...`)
- SkyMoviesHD Movie Detail Page (`/movie/....html`)
- SkyMoviesHD Category / Homepage URL

**Example Request:**
```bash
curl -s "https://your-app.onrender.com/api/extract_gdflix?url=https://howblogs.xyz/c7d100"
```
**Example JSON Response:**
```json
{
  "status": "success",
  "extracted_count": 1,
  "links": [
    {
      "title": "Linker Taker - All Your Links Take Safe",
      "label": "https://gdflix.dev/file/jh0EmXmuRpvz1ZP",
      "gdflix_url": "https://gdflix.dev/file/jh0EmXmuRpvz1ZP",
      "source_url": "https://howblogs.xyz/c7d100",
      "type": "shortener_redirect"
    }
  ]
}
```

### 3. Latest 2026 / 2025 Movies (`GET /api/latest?limit=...`)
Scrapes homepage "Latest Updated Movies" and Page 1 of all top categories, returning structured JSON with **Movie Titles, Release Year, Posters, Details URLs, and GDFlix links**.

### 4. Multi-Page Category Scraper (`GET /api/category?name=...&start_page=1&end_page=3`)
Scrapes any of the 22 categories across multiple pagination pages (`Page 1, 2, 3...`) and extracts GDFlix links concurrently.

### 5. Categories List (`GET /api/categories`)
Returns all 22 available movie categories on SkyMoviesHD.

### 6. Export Reports (`GET /api/export/{fmt}`)
Download the last scraped catalog as a file:
- `/api/export/json` → `skymovieshd_catalog.json`
- `/api/export/csv` → `skymovieshd_catalog.csv`
- `/api/export/md` → `skymovieshd_catalog.md`

---

## 🚀 How to Deploy on Render.com (1-Click / Zero Config)

This repository includes all required deployment files:
- `requirements.txt`
- `Procfile`
- `render.yaml`
- `runtime.txt`
- `app.py` & `skymovieshd_scraper.py`

### Step-by-Step Deployment:
1. **Push to GitHub**:
   - Create a repository on GitHub and upload all files from `/home/user/`.
2. **Connect on Render.com**:
   - Log in to [https://render.com](https://render.com).
   - Click **New +** → **Blueprint** (or **Web Service**).
   - Select your GitHub repo.
3. **Auto Configuration**:
   - Render automatically reads `render.yaml` / `Procfile`:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. **Deploy**:
   - Click **Apply / Create Web Service**. Within 60 seconds, your API will be live at `https://your-app.onrender.com`!

---

## 💻 Running Locally (CLI / Terminal)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run API server
python3 app.py
# Open Swagger docs at http://127.0.0.1:8000/docs
```

### Using Core Scraper via Terminal (`skymovieshd_scraper.py`):
```bash
# Extract GDFlix links from any URL
python3 skymovieshd_scraper.py --extract-url "https://howblogs.xyz/c7d100"

# Scrape all latest 2026/2025 movies
python3 skymovieshd_scraper.py --latest --workers 10

# Scrape Bollywood Movies across Pages 1 to 4
python3 skymovieshd_scraper.py --category "Bollywood Movies" --start-page 1 --end-page 4
```
