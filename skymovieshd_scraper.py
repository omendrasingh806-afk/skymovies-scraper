#!/usr/bin/env python3
"""
SkyMoviesHD.ceo Universal Scraper & GDFlix Extractor
----------------------------------------------------
Universal extractor and specialized scraping routes:
  - Universal GDFlix link extraction from ANY URL
  - Search movies/web series by keyword (`search.php`)
  - Homepage latest & popular movies extraction
  - Dedicated Web Series scraper
  - Multi-page category scraping (Page 1, 2, 3, 4...)
  - High-performance concurrent extraction (ThreadPoolExecutor)

Author: AI Assistant (Arena.ai)
Date: 2026-07-30
"""

import os
import re
import csv
import json
import time
import logging
import argparse
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SkyMoviesHDScraper")


class SkyMoviesHDScraper:
    def __init__(self, base_url="https://skymovieshd.ceo", timeout=12, max_workers=10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_workers = max_workers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get(self, url, **kwargs):
        """Helper to fetch a URL with retry logic."""
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                if resp.status_code == 200:
                    return resp
            except Exception as e:
                if attempt == 2:
                    logger.debug(f"Failed to fetch {url}: {e}")
                else:
                    time.sleep(0.4 * (attempt + 1))
        return None

    def search_movies(self, query, cat="All"):
        """Searches movies/web series on skymovieshd.ceo using search.php."""
        logger.info(f"Searching for '{query}' (category: {cat})...")
        url = f"{self.base_url}/search.php"
        resp = self._get(url, params={"search": query, "cat": cat})
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        movies = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "/movie/" in href:
                full_url = urljoin(f"{self.base_url}/", href)
                title = a.text.strip()
                if full_url not in seen_urls and title:
                    seen_urls.add(full_url)
                    year_match = re.search(r"\((\d{4})\)", title)
                    year = int(year_match.group(1)) if year_match else 0
                    movies.append({
                        "title": title,
                        "movie_url": full_url,
                        "page_found": 1,
                        "year": year,
                        "category": f"Search: {query}"
                    })

        logger.info(f"Search found {len(movies)} movies.")
        return movies

    def get_homepage_content(self):
        """Scrapes homepage MOST POPULAR MOVIES and Latest Updated Movies."""
        logger.info(f"Fetching homepage content from {self.base_url}/")
        resp = self._get(f"{self.base_url}/")
        if not resp:
            return {"popular_movies": [], "latest_movies": [], "categories": []}

        soup = BeautifulSoup(resp.text, "html.parser")
        popular_movies = []
        latest_movies = []
        seen_popular = set()
        seen_latest = set()

        # Popular movies are usually under "MOST POPULAR MOVIES"
        # Let's check div.Let vs div.Fmvideo
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            title = a.text.strip()
            if "/movie/" in href or (href.startswith("movie/") and href.endswith(".html")):
                full_url = urljoin(f"{self.base_url}/", href)
                year_match = re.search(r"\((\d{4})\)", title)
                year = int(year_match.group(1)) if year_match else 0
                item = {
                    "title": title,
                    "movie_url": full_url,
                    "year": year,
                    "category": "Homepage"
                }
                # If parent div has class Let, it's typically popular
                parent_class = a.parent.parent.get("class", []) if a.parent and a.parent.parent else []
                if "Let" in parent_class:
                    if full_url not in seen_popular:
                        seen_popular.add(full_url)
                        popular_movies.append(item)
                else:
                    if full_url not in seen_latest:
                        seen_latest.add(full_url)
                        latest_movies.append(item)

        categories = self.get_categories()
        return {
            "popular_movies": popular_movies,
            "latest_movies": latest_movies,
            "categories": categories
        }

    def universal_gdflix_extractor(self, url):
        """
        Universal GDFlix Link Extractor:
        Takes ANY URL (Direct gdflix link, Howblogs shortener, SkymoviesHD Movie Page,
        SkymoviesHD Category Page, Homepage, or any random webpage) and extracts all
        GDFlix direct download links.
        """
        url = url.strip()
        if not url:
            return []

        logger.info(f"Universal GDFlix extraction for URL: {url}")

        if "gdflix" in url.lower():
            return [{
                "title": "Direct GDFlix Link",
                "label": "Direct GDFlix File URL",
                "gdflix_url": url,
                "source_url": url,
                "type": "direct_link"
            }]

        if any(domain in url.lower() for domain in ["howblogs", "tpead", "skybap", "drive"]):
            resp = self._get(url)
            results = []
            if resp:
                soup = BeautifulSoup(resp.text, "html.parser")
                page_title = soup.title.text.strip() if soup.title else "Redirect Shortener Page"
                seen = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if "gdflix" in href and href not in seen:
                        seen.add(href)
                        results.append({
                            "title": page_title,
                            "label": a.text.strip() or "GDFlix Download Link",
                            "gdflix_url": href,
                            "source_url": url,
                            "type": "shortener_redirect"
                        })
                if not results:
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        if any(d in href for d in ["gofile", "drivehub", "hubcloud", "multicloud", "filezz", "vikingfile"]) and href not in seen:
                            seen.add(href)
                            results.append({
                                "title": page_title,
                                "label": f"[Backup Cloud] {a.text.strip() or 'Download Link'}",
                                "gdflix_url": href,
                                "source_url": url,
                                "type": "backup_cloud_link"
                            })
            return results

        if "/movie/" in url:
            movie_res = self.scrape_movie_details({"movie_url": url, "title": "Movie Page"})
            results = []
            for g in movie_res.get("gdflix_links", []):
                results.append({
                    "title": movie_res.get("title", "Unknown Movie"),
                    "label": g["label"],
                    "gdflix_url": g["url"],
                    "poster": movie_res.get("poster", ""),
                    "size": movie_res.get("size", ""),
                    "quality": movie_res.get("quality", ""),
                    "source_url": url,
                    "type": "movie_detail"
                })
            if not results:
                for o in movie_res.get("other_cloud_links", []):
                    results.append({
                        "title": movie_res.get("title", "Unknown Movie"),
                        "label": f"[Backup] {o['label']}",
                        "gdflix_url": o["url"],
                        "poster": movie_res.get("poster", ""),
                        "source_url": url,
                        "type": "backup_cloud"
                    })
            return results

        if "category/" in url or url.rstrip("/") == self.base_url:
            resp = self._get(url)
            if not resp:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            movie_items = []
            seen_m = set()
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if "/movie/" in href:
                    full_url = urljoin(f"{self.base_url}/", href)
                    if full_url not in seen_m:
                        seen_m.add(full_url)
                        movie_items.append({
                            "title": a.text.strip(),
                            "movie_url": full_url,
                            "page_found": 1
                        })
            detailed = self.scrape_movies_concurrently(movie_items[:25])
            results = []
            for m in detailed:
                for g in m.get("gdflix_links", []):
                    results.append({
                        "title": m.get("title", "Movie"),
                        "label": g["label"],
                        "gdflix_url": g["url"],
                        "poster": m.get("poster", ""),
                        "source_url": m.get("movie_url", url),
                        "type": "category_batch"
                    })
            return results

        resp = self._get(url)
        results = []
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            page_title = soup.title.text.strip() if soup.title else "Webpage"
            seen = set()
            shorteners = []

            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                label = a.text.strip() or "Link"
                if "gdflix" in href and href not in seen:
                    seen.add(href)
                    results.append({
                        "title": page_title,
                        "label": label,
                        "gdflix_url": href,
                        "source_url": url,
                        "type": "webpage_direct"
                    })
                elif any(d in href for d in ["howblogs", "tpead"]):
                    if href not in [s[1] for s in shorteners]:
                        shorteners.append((label, href))

            if shorteners:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(self.universal_gdflix_extractor, s_url) for _, s_url in shorteners]
                    for future in as_completed(futures):
                        try:
                            sub_res = future.result()
                            for sr in sub_res:
                                if sr["gdflix_url"] not in seen:
                                    seen.add(sr["gdflix_url"])
                                    results.append(sr)
                        except Exception:
                            pass

        return results

    def get_categories(self):
        """Scrapes the homepage and returns a list of dicts with category name and URL."""
        logger.info(f"Fetching categories from homepage: {self.base_url}/")
        resp = self._get(f"{self.base_url}/")
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        categories = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.text.strip()
            if "category/" in href and not href.endswith("/1.html"):
                full_url = urljoin(f"{self.base_url}/", href)
                if full_url not in seen_urls and text:
                    seen_urls.add(full_url)
                    categories.append({
                        "name": text,
                        "url": full_url,
                        "slug": href.split("/")[-1].replace(".html", "")
                    })

        return categories

    def get_page_url(self, category_url, page_num):
        """Generates the URL for a specific pagination page of a category."""
        clean_url = category_url.replace(".html", "")
        if page_num == 1:
            return f"{clean_url}.html"
        else:
            return f"{clean_url}/{page_num}.html"

    def scrape_category_page(self, category_url, page_num):
        """Scrapes a single category listing page for basic movie items."""
        page_url = self.get_page_url(category_url, page_num)
        resp = self._get(page_url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        movies = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "/movie/" in href:
                full_url = urljoin(f"{self.base_url}/", href)
                title = a.text.strip()
                if full_url not in seen_urls and title:
                    seen_urls.add(full_url)
                    year_match = re.search(r"\((\d{4})\)", title)
                    year = int(year_match.group(1)) if year_match else 0
                    movies.append({
                        "title": title,
                        "movie_url": full_url,
                        "page_found": page_num,
                        "year": year,
                        "category": "Category Listing"
                    })

        return movies

    def scrape_category_pages(self, category_url, start_page=1, end_page=4):
        """Scrapes multiple pages of a category."""
        all_movies = []
        for p in range(start_page, end_page + 1):
            page_movies = self.scrape_category_page(category_url, p)
            if not page_movies:
                break
            all_movies.extend(page_movies)
            time.sleep(0.3)
        return all_movies

    def get_latest_movies(self):
        """
        Scrapes all newly updated/released movies from the homepage and
        Page 1 of all major active categories.
        """
        logger.info("Fetching ALL LATEST & NEW MOVIES from Homepage and Top Categories...")
        all_movies = []
        seen_urls = set()

        resp = self._get(f"{self.base_url}/")
        if resp:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if "/movie/" in href:
                    full_url = urljoin(f"{self.base_url}/", href)
                    title = a.text.strip()
                    if full_url not in seen_urls and title:
                        seen_urls.add(full_url)
                        year_match = re.search(r"\((\d{4})\)", title)
                        year = int(year_match.group(1)) if year_match else 0
                        all_movies.append({
                            "title": title,
                            "movie_url": full_url,
                            "page_found": 1,
                            "year": year,
                            "category": "Homepage (Latest/Popular)"
                        })

        top_category_slugs = [
            "Bollywood-Movies.html",
            "South-Indian-Hindi-Dubbed-Movies.html",
            "Hollywood-Hindi-Dubbed-Movies.html",
            "Hollywood-English-Movies.html",
            "All-Web-Series.html",
            "Punjabi-Movies.html",
            "Bengali-Movies.html",
            "Pakistani-Movies.html"
        ]

        for slug in top_category_slugs:
            cat_url = f"{self.base_url}/category/{slug}"
            cat_name = slug.replace(".html", "").replace("-", " ")
            page_movies = self.scrape_category_page(cat_url, 1)
            for m in page_movies:
                if m["movie_url"] not in seen_urls:
                    seen_urls.add(m["movie_url"])
                    m["category"] = cat_name
                    all_movies.append(m)
            time.sleep(0.2)

        all_movies.sort(key=lambda x: (-x.get("year", 0), x.get("title", "")))
        return all_movies

    def scrape_movie_details(self, movie_item):
        """
        Visits a movie detail page, extracts poster and metadata,
        and follows redirect links to extract GDFlix and other direct cloud links.
        """
        movie_url = movie_item["movie_url"]
        resp = self._get(movie_url)
        if not resp:
            return movie_item

        soup = BeautifulSoup(resp.text, "html.parser")

        title = movie_item.get("title")
        t_div = soup.find("div", class_="Robiul")
        if t_div and t_div.find("b"):
            t_text = t_div.find("b").text.strip()
            if len(t_text) > len(title):
                title = t_text
        if not title and soup.title:
            title = soup.title.text.strip().replace("Full Movie Download", "").strip()

        year_match = re.search(r"\((\d{4})\)", title)
        year = int(year_match.group(1)) if year_match else movie_item.get("year", 0)

        poster = None
        m_list = soup.find("div", class_="movielist")
        if m_list and m_list.find("img"):
            poster = m_list.find("img").get("src")
        if not poster:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if any(domain in src for domain in ["media-amazon.com", "bmscdn.com", "imageflix", "ltrbxd.com", "imdb"]):
                    poster = src
                    break

        metadata = {}
        for div in soup.find_all("div", class_="Let"):
            text = div.text.strip()
            if ":" in text:
                parts = text.split(":", 1)
                metadata[parts[0].strip().lower()] = parts[1].strip()

        redirect_links = []
        seen_redirects = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.text.strip()
            if "howblogs" in href or "tpead" in href or any(kw in text.lower() for kw in ["google drive", "server", "480p", "720p", "1080p", "links", "hevc"]):
                if href not in seen_redirects and not href.endswith(".html"):
                    seen_redirects.add(href)
                    redirect_links.append({"label": text, "redirect_url": href})

        gdflix_links = []
        other_cloud_links = []
        seen_gdflix = set()
        seen_other = set()

        for r_item in redirect_links:
            r_url = r_item["redirect_url"]
            label = r_item["label"]
            if "howblogs" in r_url:
                r_resp = self._get(r_url)
                if r_resp:
                    r_soup = BeautifulSoup(r_resp.text, "html.parser")
                    for a in r_soup.find_all("a", href=True):
                        href = a["href"].strip()
                        if "gdflix" in href:
                            if href not in seen_gdflix:
                                seen_gdflix.add(href)
                                gdflix_links.append({
                                    "label": label,
                                    "url": href
                                })
                        elif any(domain in href for domain in ["gofile", "drivehub", "hubcloud", "multicloud", "filezz", "vikingfile", "usersdrive", "uploadg"]):
                            if href not in seen_other:
                                seen_other.add(href)
                                other_cloud_links.append({
                                    "label": label,
                                    "url": href
                                })

        result = {
            "title": title,
            "year": year,
            "category": movie_item.get("category", "Category Listing"),
            "movie_url": movie_url,
            "poster": poster or "N/A",
            "page_found": movie_item.get("page_found", 1),
            "size": metadata.get("size", "N/A"),
            "language": metadata.get("language", "N/A"),
            "quality": metadata.get("quality", "N/A"),
            "gdflix_links": gdflix_links,
            "gdflix_count": len(gdflix_links),
            "other_cloud_links": other_cloud_links,
            "other_count": len(other_cloud_links),
            "redirect_count": len(redirect_links)
        }
        return result

    def scrape_movies_concurrently(self, movie_items):
        """Scrapes movie details in parallel using ThreadPoolExecutor."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_movie = {
                executor.submit(self.scrape_movie_details, item): item
                for item in movie_items
            }
            for future in as_completed(future_to_movie):
                item = future_to_movie[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Error scraping {item['movie_url']}: {e}")
                    results.append(item)

        results.sort(key=lambda x: (-x.get("year", 0), x.get("title", "")))
        return results

    def save_to_json(self, movies, filepath):
        """Exports scraped movie catalog to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"total_movies": len(movies), "movies": movies}, f, indent=2, ensure_ascii=False)

    def save_to_csv(self, movies, filepath):
        """Exports scraped movie catalog to CSV file."""
        fieldnames = [
            "year", "category", "title", "poster", "movie_url",
            "gdflix_count", "gdflix_links", "other_count", "other_cloud_links",
            "size", "language", "quality"
        ]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in movies:
                row = {
                    "year": m.get("year", ""),
                    "category": m.get("category", ""),
                    "title": m.get("title", ""),
                    "poster": m.get("poster", ""),
                    "movie_url": m.get("movie_url", ""),
                    "gdflix_count": m.get("gdflix_count", 0),
                    "gdflix_links": " ; ".join([f"{x['label']}: {x['url']}" for x in m.get("gdflix_links", [])]),
                    "other_count": m.get("other_count", 0),
                    "other_cloud_links": " ; ".join([f"{x['label']}: {x['url']}" for x in m.get("other_cloud_links", [])]),
                    "size": m.get("size", ""),
                    "language": m.get("language", ""),
                    "quality": m.get("quality", "")
                }
                writer.writerow(row)

    def save_to_markdown(self, movies, filepath, title_header="SkyMoviesHD Scraped Catalog"):
        """Exports scraped movie catalog to a formatted Markdown report."""
        lines = []
        lines.append(f"# 🎬 {title_header}\n")
        lines.append(f"- **Total Movies Scraped**: {len(movies)}")
        lines.append(f"- **Generated on**: 2026-07-30\n")

        lines.append("## 📊 Summary Table\n")
        lines.append("| Year | Category | Movie Title | Poster | Details Page | GDFlix Links | Other Cloud Links |")
        lines.append("| :--: | :--- | :--- | :---: | :--- | :--- | :--- |")

        for m in movies:
            year = m.get("year", "N/A")
            cat = m.get("category", "General")
            title = m.get("title", "Unknown")
            poster = m.get("poster", "")
            poster_md = f"[🖼️ Poster]({poster})" if poster and poster != "N/A" else "N/A"
            m_url = m.get("movie_url", "")
            m_link = f"[🔗 Details]({m_url})" if m_url else "N/A"

            gdflix_list = m.get("gdflix_links", [])
            if gdflix_list:
                gdflix_md = "<br>".join([f"• [{item['label']}]({item['url']})" for item in gdflix_list])
            else:
                gdflix_md = "*No GDFlix Link Found*"

            other_list = m.get("other_cloud_links", [])
            if other_list:
                other_md = "<br>".join([f"• [{item['label']}]({item['url']})" for item in other_list[:3]])
                if len(other_list) > 3:
                    other_md += f"<br>*(+{len(other_list)-3} more)*"
            else:
                other_md = "N/A"

            lines.append(f"| **{year}** | **{cat}** | **{title}** | {poster_md} | {m_link} | {gdflix_md} | {other_md} |")

        lines.append("\n---\n")
        lines.append("## 📁 Detailed Movie Cards\n")

        for m in movies:
            lines.append(f"### 🎞️ {m.get('title')}\n")
            lines.append(f"- **Category**: {m.get('category', 'N/A')}")
            lines.append(f"- **Movie Details URL**: [{m.get('movie_url')}]({m.get('movie_url')})")
            lines.append(f"- **Poster Image**: [{m.get('poster')}]({m.get('poster')})")
            if m.get("size", "N/A") != "N/A":
                lines.append(f"- **Size**: {m.get('size')} | **Language**: {m.get('language')} | **Quality**: {m.get('quality')}")

            lines.append("\n#### 🚀 GDFlix Direct Links")
            gdflix_list = m.get("gdflix_links", [])
            if gdflix_list:
                for idx, g in enumerate(gdflix_list, 1):
                    lines.append(f"{idx}. **{g['label']}** → [`{g['url']}`]({g['url']})")
            else:
                lines.append("- *(No direct GDFlix links found for this movie)*")

            other_list = m.get("other_cloud_links", [])
            if other_list:
                lines.append("\n#### 🌐 Other Cloud / Backup Links")
                for idx, o in enumerate(other_list, 1):
                    lines.append(f"{idx}. **{o['label']}** → [`{o['url']}`]({o['url']})")

            lines.append("\n---\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="SkyMoviesHD Scraper (Homepage, Search, Web Series, Multi-Page, Universal GDFlix)")
    parser.add_argument("--extract-url", type=str, help="Universal mode: Extract GDFlix links from ANY URL")
    parser.add_argument("--search", type=str, help="Search movies/web series by keyword")
    parser.add_argument("--latest", action="store_true", help="Scrape all new & latest movies across homepage and top categories")
    parser.add_argument("--home", action="store_true", help="Scrape homepage popular & latest movies")
    parser.add_argument("--list-categories", action="store_true", help="List all available categories on the homepage")
    parser.add_argument("--category", type=str, default="Bollywood Movies", help="Category name or slug to scrape")
    parser.add_argument("--start-page", type=int, default=1, help="Starting page number")
    parser.add_argument("--end-page", type=int, default=2, help="Ending page number")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent threads")
    parser.add_argument("--out-json", type=str, default="skymovieshd_catalog.json", help="Output JSON filepath")
    parser.add_argument("--out-csv", type=str, default="skymovieshd_catalog.csv", help="Output CSV filepath")
    parser.add_argument("--out-md", type=str, default="skymovieshd_catalog.md", help="Output Markdown filepath")

    args = parser.parse_args()
    scraper = SkyMoviesHDScraper(max_workers=args.workers)

    if args.extract_url:
        results = scraper.universal_gdflix_extractor(args.extract_url)
        print(f"\n================ GDFlix Extracted Results ({len(results)} links) ================")
        for idx, res in enumerate(results, 1):
            print(f"{idx}. [{res['label']}] -> {res['gdflix_url']}")
        print("=========================================================================\n")
        return

    if args.search:
        movie_items = scraper.search_movies(args.search)
        detailed = scraper.scrape_movies_concurrently(movie_items)
        scraper.save_to_json(detailed, args.out_json)
        scraper.save_to_markdown(detailed, args.out_md, title_header=f"SkyMoviesHD Search Results: {args.search}")
        print(f"\n✅ Scraped {len(detailed)} search results for '{args.search}'!")
        return

    if args.home:
        data = scraper.get_homepage_content()
        detailed_pop = scraper.scrape_movies_concurrently(data["popular_movies"])
        detailed_lat = scraper.scrape_movies_concurrently(data["latest_movies"])
        all_home = detailed_pop + detailed_lat
        scraper.save_to_json(all_home, args.out_json)
        scraper.save_to_markdown(all_home, args.out_md, title_header="SkyMoviesHD Homepage Catalog")
        print(f"\n✅ Scraped {len(all_home)} homepage movies!")
        return

    if args.list_categories:
        categories = scraper.get_categories()
        print("\n================ AVAILABLE CATEGORIES ================")
        for idx, cat in enumerate(categories, 1):
            print(f"{idx:2d}. {cat['name']} -> {cat['url']}")
        print("======================================================\n")
        return

    if args.latest:
        movie_items = scraper.get_latest_movies()
        detailed_movies = scraper.scrape_movies_concurrently(movie_items)
        scraper.save_to_json(detailed_movies, args.out_json)
        scraper.save_to_csv(detailed_movies, args.out_csv)
        scraper.save_to_markdown(detailed_movies, args.out_md, title_header="SkyMoviesHD — LATEST & NEWEST MOVIES CATALOG")
        print(f"\n✅ Scraped {len(detailed_movies)} LATEST movies from Homepage & Top Categories!")
        return

    # Category multi-page scraping
    categories = scraper.get_categories()
    target_cat = None
    for cat in categories:
        if args.category.lower() in cat["name"].lower() or args.category.lower() in cat["slug"].lower():
            target_cat = cat
            break

    if not target_cat:
        if args.category.startswith("http"):
            target_cat = {"name": "Custom Category", "url": args.category, "slug": "custom"}
        else:
            return

    movie_items = scraper.scrape_category_pages(
        category_url=target_cat["url"],
        start_page=args.start_page,
        end_page=args.end_page
    )

    detailed_movies = scraper.scrape_movies_concurrently(movie_items)
    scraper.save_to_json(detailed_movies, args.out_json)
    scraper.save_to_csv(detailed_movies, args.out_csv)
    scraper.save_to_markdown(detailed_movies, args.out_md, title_header=f"SkyMoviesHD Scraped Catalog: {target_cat['name']}")
    print(f"\n✅ Scraped {len(detailed_movies)} movies from '{target_cat['name']}' across pages {args.start_page} to {args.end_page}!")


if __name__ == "__main__":
    main()
