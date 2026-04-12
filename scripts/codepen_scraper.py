#!/usr/bin/env python3
"""
CodePen Creative Code Scraper for Cipher Code Kraken Training Data.

Searches CodePen for pens tagged with creative-dev keywords (GSAP, Three.js,
WebGL, Lenis, shaders, etc.), extracts HTML/CSS/JS sections, and outputs
structured JSONL for the training pipeline.

Usage:
    python scripts/codepen_scraper.py --output data/raw/codepen.jsonl
    python scripts/codepen_scraper.py --output data/raw/codepen.jsonl --max-pens 200
"""

import argparse
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

# ─── Configuration ────────────────────────────────────────────────────────────

SEARCH_TAGS = [
    "gsap",
    "threejs",
    "webgl",
    "creative-coding",
    "scrolltrigger",
    "lenis",
    "shader",
]

# CodePen search URL pattern
SEARCH_URL = "https://codepen.io/search/pens"

# Rate limiting: seconds between requests
REQUEST_DELAY = 1.0

# Minimum JS lines to keep a pen (skip trivially short pens)
MIN_JS_LINES = 15

# User agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    """Log progress to stderr so stdout stays clean for JSONL."""
    print(msg, file=sys.stderr, flush=True)


def get_session() -> requests.Session:
    """Create a requests session with appropriate headers."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def line_count(text: str) -> int:
    """Count non-empty lines in text."""
    if not text:
        return 0
    return len([line for line in text.split("\n") if line.strip()])


# ─── Search & Extraction ─────────────────────────────────────────────────────


def search_pens_by_tag(session: requests.Session, tag: str, max_pages: int = 50) -> list[dict]:
    """
    Search CodePen for pens matching a tag. Returns list of pen metadata dicts.
    Each dict: {"pen_id": str, "author": str, "title": str, "url": str}
    """
    pens = []

    for page in range(1, max_pages + 1):
        try:
            time.sleep(REQUEST_DELAY)
            resp = session.get(
                SEARCH_URL,
                params={"q": tag, "page": page},
                timeout=30,
            )
            if resp.status_code != 200:
                log(f"[search] HTTP {resp.status_code} for tag '{tag}' page {page}, stopping")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            # CodePen search results are in data attributes or pen items
            pen_items = soup.select("[data-slug-hash]")
            if not pen_items:
                # Alternative: look for pen links
                pen_links = soup.select("a[href*='/pen/']")
                if not pen_links:
                    log(f"[search] No more results for tag '{tag}' at page {page}")
                    break

                for link in pen_links:
                    href = link.get("href", "")
                    # Extract pen ID from URL like /username/pen/AbCdEf
                    match = re.search(r"/pen/([a-zA-Z0-9]+)", href)
                    if match:
                        pen_id = match.group(1)
                        # Extract author from URL
                        author_match = re.search(r"codepen\.io/([^/]+)/pen/", href)
                        if not author_match:
                            author_match = re.search(r"/([^/]+)/pen/", href)
                        author = author_match.group(1) if author_match else "unknown"
                        title = link.get_text(strip=True) or pen_id

                        pens.append(
                            {
                                "pen_id": pen_id,
                                "author": author,
                                "title": title,
                                "url": f"https://codepen.io/{author}/pen/{pen_id}",
                            }
                        )
            else:
                for item in pen_items:
                    pen_id = item.get("data-slug-hash", "")
                    author = item.get("data-user", "") or "unknown"
                    title_el = item.select_one(".pen-title, h3, [class*='title']")
                    title = title_el.get_text(strip=True) if title_el else pen_id

                    if pen_id:
                        pens.append(
                            {
                                "pen_id": pen_id,
                                "author": author,
                                "title": title,
                                "url": f"https://codepen.io/{author}/pen/{pen_id}",
                            }
                        )

            log(f"[search] Tag '{tag}' page {page}: found {len(pen_items or pen_links)} pens (total: {len(pens)})")

        except requests.RequestException as e:
            log(f"[search] Network error on tag '{tag}' page {page}: {e}")
            break
        except Exception as e:
            log(f"[search] Error on tag '{tag}' page {page}: {e}")
            break

    return pens


def fetch_pen_content(session: requests.Session, pen_id: str, author: str) -> dict | None:
    """
    Fetch the actual HTML, CSS, and JS content of a CodePen pen.
    Uses the embed/preview endpoint to extract code sections.
    Returns dict with 'html', 'css', 'js' keys, or None on failure.
    """
    # Try the pen's direct page first
    urls_to_try = [
        f"https://codepen.io/{author}/pen/{pen_id}",
        f"https://codepen.io/{author}/details/{pen_id}",
    ]

    for url in urls_to_try:
        try:
            time.sleep(REQUEST_DELAY)
            resp = session.get(url, timeout=30)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract code from various possible containers
            html_code = ""
            css_code = ""
            js_code = ""

            # Method 1: Look for pre/code elements with language indicators
            for pre in soup.select("pre"):
                classes = " ".join(pre.get("class", []))
                text = pre.get_text()
                if "html" in classes.lower():
                    html_code = text
                elif "css" in classes.lower():
                    css_code = text
                elif "js" in classes.lower() or "javascript" in classes.lower():
                    js_code = text

            # Method 2: Look for textareas or hidden inputs with pen content
            if not js_code:
                for textarea in soup.select("textarea, [data-type]"):
                    data_type = textarea.get("data-type", "").lower()
                    text = textarea.get_text()
                    if data_type == "html" or textarea.get("id", "").endswith("html"):
                        html_code = html_code or text
                    elif data_type == "css" or textarea.get("id", "").endswith("css"):
                        css_code = css_code or text
                    elif data_type in ("js", "javascript") or textarea.get("id", "").endswith("js"):
                        js_code = js_code or text

            # Method 3: Look for __NEXT_DATA__ or embedded JSON with pen data
            if not js_code:
                for script in soup.select("script"):
                    script_text = script.get_text()
                    if "__pen" in script_text or "penData" in script_text:
                        # Try to extract JSON pen data
                        try:
                            json_match = re.search(r"\{.*\"js\".*\}", script_text, re.DOTALL)
                            if json_match:
                                data = json.loads(json_match.group())
                                html_code = html_code or data.get("html", "")
                                css_code = css_code or data.get("css", "")
                                js_code = js_code or data.get("js", "")
                        except (json.JSONDecodeError, AttributeError):
                            pass

            if html_code or css_code or js_code:
                return {"html": html_code, "css": css_code, "js": js_code}

        except requests.RequestException as e:
            log(f"[fetch] Network error fetching pen {pen_id}: {e}")
            continue
        except Exception as e:
            log(f"[fetch] Error fetching pen {pen_id}: {e}")
            continue

    return None


def combine_pen_content(html: str, css: str, js: str) -> str:
    """
    Combine HTML, CSS, and JS sections into a single content string
    with clear section markers.
    """
    parts = []

    if html and html.strip():
        parts.append(f"// === HTML ===\n{html.strip()}")
    if css and css.strip():
        parts.append(f"// === CSS ===\n{css.strip()}")
    if js and js.strip():
        parts.append(f"// === JS ===\n{js.strip()}")

    return "\n\n".join(parts)


# ─── Main Pipeline ────────────────────────────────────────────────────────────


def scrape_codepen(max_pens: int, output_path: str) -> None:
    """
    Main scraping pipeline: search tags, fetch pen content, output JSONL.
    """
    session = get_session()

    # Discover pens across all tags
    all_pens = []
    seen_ids = set()

    for tag in SEARCH_TAGS:
        log(f"[discover] Searching tag: {tag}")
        pens = search_pens_by_tag(session, tag)

        for pen in pens:
            if pen["pen_id"] not in seen_ids:
                seen_ids.add(pen["pen_id"])
                pen["tags"] = [tag]
                all_pens.append(pen)
            else:
                # Add tag to existing pen
                for existing in all_pens:
                    if existing["pen_id"] == pen["pen_id"]:
                        if tag not in existing.get("tags", []):
                            existing.setdefault("tags", []).append(tag)
                        break

        log(f"[discover] Total unique pens after tag '{tag}': {len(all_pens)}")

        if len(all_pens) >= max_pens:
            log(f"[discover] Reached max_pens limit ({max_pens})")
            all_pens = all_pens[:max_pens]
            break

    log(f"[discover] Total unique pens discovered: {len(all_pens)}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    total_extracted = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for i, pen in enumerate(all_pens):
            log(f"[scrape] ({i + 1}/{len(all_pens)}) Fetching pen {pen['pen_id']} by {pen['author']}")

            content = fetch_pen_content(session, pen["pen_id"], pen["author"])
            if not content:
                log(f"[scrape] Could not extract content from pen {pen['pen_id']}, skipping")
                continue

            # Check JS line count threshold
            js_lines = line_count(content.get("js", ""))
            if js_lines < MIN_JS_LINES:
                log(f"[scrape] Pen {pen['pen_id']} JS too short ({js_lines} lines), skipping")
                continue

            # Combine sections
            combined = combine_pen_content(
                content.get("html", ""),
                content.get("css", ""),
                content.get("js", ""),
            )

            record = {
                "source": "codepen",
                "pen_id": pen["pen_id"],
                "author": pen["author"],
                "title": pen.get("title", ""),
                "content": combined,
                "tags": pen.get("tags", []),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            total_extracted += 1

    log(f"[scrape] Complete. {total_extracted} pens written to {output_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape creative code from CodePen for Cipher training data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/codepen_scraper.py --output data/raw/codepen.jsonl
  python scripts/codepen_scraper.py --output data/raw/codepen.jsonl --max-pens 200

Tags searched: gsap, threejs, webgl, creative-coding, scrolltrigger, lenis, shader

Output format (JSONL):
  {"source": "codepen", "pen_id": "...", "author": "...", "title": "...",
   "content": "...", "tags": [...]}
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path for JSONL data (e.g., data/raw/codepen.jsonl)",
    )
    parser.add_argument(
        "--max-pens",
        type=int,
        default=1000,
        help="Maximum number of pens to process (default: 1000)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scrape_codepen(args.max_pens, args.output)


if __name__ == "__main__":
    main()
