#!/usr/bin/env python3
"""
SkyMoviesHD Universal GDFlix Scraper — Pure FastAPI Backend API
---------------------------------------------------------------
Render / Heroku / Railway Deployment Ready REST API Service (No UI).

Endpoints:
  - GET  /                        -> JSON Health Check & Endpoints Overview
  - GET  /docs                    -> Swagger UI Interactive API Documentation
  - GET  /api/extract_gdflix      -> Universal extractor for ANY URL (?url=https://...)
  - GET  /api/latest              -> Returns JSON of newest 2026/2025 movies with GDFlix links
  - GET  /api/category            -> Multi-page category scraper (?name=Bollywood&start_page=1&end_page=2)
  - GET  /api/categories          -> Lists all 22 available movie categories
  - GET  /api/export/{fmt}        -> Download report as json, csv, or md

Author: AI Assistant (Arena.ai)
Date: 2026-07-30
"""

import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from skymovieshd_scraper import SkyMoviesHDScraper

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SkyMoviesHDBackend")

app = FastAPI(
    title="SkyMoviesHD Universal GDFlix Scraper API",
    description="Pure REST API backend to scrape SkyMoviesHD movies and extract GDFlix cloud download links from any URL.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Scraper Instance & In-memory result cache for instant exports
max_workers = int(os.environ.get("MAX_WORKERS", 10))
scraper = SkyMoviesHDScraper(max_workers=max_workers)
last_scraped_catalog = []


@app.get("/", response_class=JSONResponse)
async def serve_root():
    """Returns JSON Service Info and available REST API endpoints."""
    return {
        "service": "SkyMoviesHD Universal GDFlix Scraper API",
        "version": "2.0.0",
        "status": "online",
        "swagger_documentation": "/docs",
        "redoc_documentation": "/redoc",
        "endpoints": {
            "extract_gdflix": "/api/extract_gdflix?url={any_url}",
            "latest_movies": "/api/latest?limit={optional_limit}",
            "category_scraper": "/api/category?name=Bollywood Movies&start_page=1&end_page=2",
            "list_categories": "/api/categories",
            "export_last_scrape": "/api/export/{json|csv|md}"
        }
    }


@app.get("/api/extract_gdflix", response_class=JSONResponse)
async def api_extract_gdflix(
    url: str = Query(..., description="Any URL (Movie Page, Category, HowBlogs/Tpead redirect, or direct link)")
):
    """
    Universal GDFlix Link Extractor:
    'khi par bhi sare links me se gdflix ki link ko nikal kar dega'
    """
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter cannot be empty.")

    try:
        logger.info(f"API Request -> extract_gdflix for: {url}")
        results = scraper.universal_gdflix_extractor(url)
        return {
            "status": "success",
            "extracted_count": len(results),
            "links": results
        }
    except Exception as e:
        logger.error(f"Error extracting from {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/latest", response_class=JSONResponse)
async def api_latest_movies(
    limit: Optional[int] = Query(None, description="Optional cap on total movies returned")
):
    """Fetches all newly updated & newest 2026/2025 movies across homepage and top categories."""
    global last_scraped_catalog
    try:
        logger.info("API Request -> latest_movies")
        movie_items = scraper.get_latest_movies()
        if limit:
            movie_items = movie_items[:limit]
        detailed = scraper.scrape_movies_concurrently(movie_items)
        last_scraped_catalog = detailed
        return {
            "status": "success",
            "total_movies": len(detailed),
            "movies": detailed
        }
    except Exception as e:
        logger.error(f"Error fetching latest movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/category", response_class=JSONResponse)
async def api_scrape_category(
    name: str = Query("Bollywood Movies", description="Category name or slug"),
    start_page: int = Query(1, ge=1, le=100, description="Start page number"),
    end_page: int = Query(2, ge=1, le=100, description="End page number"),
    limit: Optional[int] = Query(None, description="Optional cap on movies")
):
    """Scrapes multiple pages of any category and returns movies with GDFlix links."""
    global last_scraped_catalog
    try:
        logger.info(f"API Request -> scrape_category '{name}' (p{start_page} to p{end_page})")
        categories = scraper.get_categories()
        target_cat = None
        for cat in categories:
            if name.lower() in cat["name"].lower() or name.lower() in cat["slug"].lower():
                target_cat = cat
                break

        if not target_cat:
            target_cat = {
                "name": name,
                "url": f"{scraper.base_url}/category/{name.replace(' ', '-')}.html",
                "slug": name
            }

        movie_items = scraper.scrape_category_pages(
            category_url=target_cat["url"],
            start_page=start_page,
            end_page=end_page
        )
        if limit:
            movie_items = movie_items[:limit]

        detailed = scraper.scrape_movies_concurrently(movie_items)
        last_scraped_catalog = detailed
        return {
            "status": "success",
            "category": target_cat["name"],
            "start_page": start_page,
            "end_page": end_page,
            "total_movies": len(detailed),
            "movies": detailed
        }
    except Exception as e:
        logger.error(f"Error scraping category '{name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories", response_class=JSONResponse)
async def api_list_categories():
    """Returns all 22 available movie categories from the homepage."""
    try:
        logger.info("API Request -> list_categories")
        categories = scraper.get_categories()
        return {
            "status": "success",
            "count": len(categories),
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{fmt}")
async def api_export_catalog(fmt: str):
    """Downloads the last scraped catalog as JSON, CSV, or Markdown."""
    global last_scraped_catalog
    if not last_scraped_catalog:
        json_path = "/home/user/skymovieshd_latest_movies.json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_scraped_catalog = data.get("movies", [])

    if fmt.lower() == "json":
        filepath = "/home/user/export_catalog.json"
        scraper.save_to_json(last_scraped_catalog, filepath)
        return FileResponse(filepath, media_type="application/json", filename="skymovieshd_catalog.json")
    elif fmt.lower() == "csv":
        filepath = "/home/user/export_catalog.csv"
        scraper.save_to_csv(last_scraped_catalog, filepath)
        return FileResponse(filepath, media_type="text/csv", filename="skymovieshd_catalog.csv")
    elif fmt.lower() == "md":
        filepath = "/home/user/export_catalog.md"
        scraper.save_to_markdown(last_scraped_catalog, filepath, title_header="SkyMoviesHD Exported Catalog")
        return FileResponse(filepath, media_type="text/markdown", filename="skymovieshd_catalog.md")
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use json, csv, or md.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting SkyMoviesHD Pure Backend API on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
