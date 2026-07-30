# 🚀 SkyMoviesHD Universal GDFlix Scraper — Pure REST API Backend

**Render / Heroku / Railway / Docker Deployable Pure Backend (FastAPI)**  
*Universal GDFlix Cloud Download Link Extractor, Search Engine & Catalog Scraper for SkyMoviesHD.ceo*

---

## ✨ Available REST API Endpoints

| Route Endpoint | HTTP Method | Purpose | Example Query URL |
| :--- | :--- | :--- | :--- |
| **`/`** | `GET` | Service Status & API Map | `https://your-app.onrender.com/` |
| **`/docs`** | `GET` | Interactive Swagger API Documentation | `https://your-app.onrender.com/docs` |
| **`/api/home`** | `GET` | **Home Page**: Returns Popular Movies, Latest Updated Movies, and 22 Categories | `/api/home` |
| **`/api/search`** | `GET` | **Search**: Search movies/web series by keyword & category filter | `/api/search?query=chopsticks&cat=All` |
| **`/api/web_series`** | `GET` | **Web Series**: Scrape All Web Series category across pages | `/api/web_series?start_page=1&end_page=2` |
| **`/api/movie`** | `GET` | **Single Movie Details**: Scrape details & GDFlix links for a specific movie page | `/api/movie?url=https://skymovieshd.ceo/movie/...` |
| **`/api/extract_gdflix`** | `GET` | **Universal Extractor**: Extract GDFlix links from any URL | `/api/extract_gdflix?url=https://howblogs.xyz/c7d100` |
| **`/api/latest`** | `GET` | **Latest Releases**: Scrape newest 2026/2025 movies | `/api/latest?limit=50` |
| **`/api/category`** | `GET` | **Multi-Page Category**: Scrape any category across pages | `/api/category?name=Bollywood Movies&start_page=1&end_page=2` |
| **`/api/categories`** | `GET` | **Categories List**: Returns all 22 available categories | `/api/categories` |
| **`/api/export/{fmt}`** | `GET` | **Export**: Download report as `json`, `csv`, or `md` | `/api/export/md` |

---

## ⚡ Route Usage Details & Examples

### 1. Home Page Route (`GET /api/home`)
Scrapes `https://skymovieshd.ceo/` and returns structured JSON:
- `popular_movies`: List of Most Popular Movies with GDFlix links.
- `latest_movies`: List of Latest Updated Movies with GDFlix links.
- `categories`: All 22 available movie categories.

**Example Response:**
```json
{
  "status": "success",
  "popular_count": 19,
  "latest_count": 15,
  "categories_count": 22,
  "popular_movies": [ ... ],
  "latest_movies": [ ... ],
  "categories": [ ... ]
}
```

### 2. Search Movies & Web Series (`GET /api/search?query=...&cat=All`)
Searches the SkyMoviesHD catalog by keyword and automatically extracts GDFlix links for matching results.
- `query`: The search string (e.g. `chopsticks`, `marvel`, `pushpa`, `web series`).
- `cat`: Optional filter (`All`, `Bollywood Movies`, `All Web Series`, `South Indian Hindi Dubbed Movies`, etc.).

**Example Request:**
```bash
curl -s "https://your-app.onrender.com/api/search?query=chopsticks&cat=All"
```

### 3. Web Series Route (`GET /api/web_series?start_page=1&end_page=2`)
Dedicated endpoint to browse and scrape the **All Web Series** category across pagination pages (`Page 1, 2, 3...`) with GDFlix links.

### 4. Single Movie Details Route (`GET /api/movie?url=...`)
Scrapes a single movie details page and returns:
- `title`, `year`, `poster`, `size`, `language`, `quality`
- `gdflix_links`: All direct `gdflix.dev/file/...` download URLs.
- `other_cloud_links`: Backup cloud host links (`gofile.io`, `hubcloud`, etc.).

---

## 🚀 Render.com Deployment Settings

When deploying on **Render.com** (Web Service):
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Root Directory**: *(Leave blank)*
- **Environment Variables**:
  - `PYTHONUNBUFFERED` = `true`
  - `MAX_WORKERS` = `10`
