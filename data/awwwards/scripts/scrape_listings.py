"""Scrape Awwwards Site-of-the-Day listings.

Produces: data/awwwards/listings.jsonl — one JSON record per winner.

Schema:
    {
        "rank": 1,
        "awwwards_url": "https://www.awwwards.com/sites/example",
        "slug": "example",
        "live_url": "https://example.com",
        "title": "Example Studio",
        "agency": "Acme Co",
        "score": 6.78,
        "category": "SOTD",
        "date": "2026-04-10",
        "thumbnail": "https://..."
    }

Usage:
    python scrape_listings.py --count 100 [--offset 0]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterator

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

BASE = "https://www.awwwards.com"
LISTING_URL = BASE + "/websites/sites_of_the_day/"

OUT = Path(__file__).resolve().parent.parent / "listings.jsonl"


def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    # best-effort decode
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# --- HTML parsing (lightweight, no external deps) ----------------------------

# Awwwards wraps each card in:
#   <li class="... js-collectable" data-controller="collectable"
#       data-collectable-model-value="{&quot;slug&quot;:...,&quot;title&quot;:...,
#                                      &quot;createdAt&quot;:<unix>,
#                                      &quot;tags&quot;:[...], ...}">
#     ...
#     <a class="figure-rollover__bt" href="{LIVE_URL}" ... data-visit-count-identifier-value="{slug}">
#     <figure class="avatar-name"><a href="/{agency_slug}/">...<h3>{agency}</h3>
#     <span style="...">Mar 15, 2026</span>   <- SOTD award date
#     <span class="budget-tag budget-tag--{sotd|dev|hon}">...
#   </li>
#
# We extract the JSON in data-collectable-model-value for the canonical fields,
# then pull the live URL + award date + award tags from the surrounding HTML.

ITEM_RE = re.compile(
    # Capture the ENTIRE <li ...>...</li> (including li attrs which carry
    # the data-collectable-model-value JSON).
    r'(<li\s+class="[^"]*js-collectable[^"]*"[^>]*>.*?</li>)',
    re.IGNORECASE | re.DOTALL,
)

MODEL_RE = re.compile(
    r'data-collectable-model-value="([^"]+)"',
    re.IGNORECASE,
)

LIVE_URL_RE = re.compile(
    r'<a[^>]+class="[^"]*figure-rollover__bt[^"]*"[^>]+href="(https?://[^"]+)"[^>]+data-visit-count-identifier-value="([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)

AGENCY_RE = re.compile(
    r'<h3\s+class="[^"]*avatar-name__title[^"]*"[^>]*>\s*([^<]+?)\s*</h3>',
    re.IGNORECASE,
)

AGENCY_URL_RE = re.compile(
    r'<a[^>]+class="[^"]*avatar-name__link[^"]*"[^>]+href="([^"]+)"',
    re.IGNORECASE,
)

AWARD_DATE_RE = re.compile(
    r'style="display: block; margin-top: 10px;">\s*([A-Za-z]{3}\s+\d{1,2},\s+\d{4})',
    re.IGNORECASE,
)

AWARD_TAGS_RE = re.compile(
    r'class="[^"]*budget-tag\s+budget-tag--([a-z0-9]+)[^"]*"',
    re.IGNORECASE,
)


def _unescape(s: str) -> str:
    """Decode HTML entities (quot/amp/lt/gt/backslash-escaped unicode)."""
    out = (
        s.replace("&quot;", '"')
         .replace("&amp;", "&")
         .replace("&lt;", "<")
         .replace("&gt;", ">")
         .replace("&#039;", "'")
    )
    # Handle \/  slash-escape used inside JSON
    return out.replace("\\/", "/")


def parse_listing_page(html: str) -> Iterator[dict]:
    n_total = 0
    n_no_model = 0
    n_bad_json = 0
    n_no_slug = 0
    for m in ITEM_RE.finditer(html):
        n_total += 1
        card = m.group(1)
        mm = MODEL_RE.search(card)
        if not mm:
            n_no_model += 1
            continue
        try:
            model = json.loads(_unescape(mm.group(1)))
        except json.JSONDecodeError as e:
            n_bad_json += 1
            if n_bad_json <= 2:
                print(f"      [json err] {e}: {mm.group(1)[:200]}", file=sys.stderr)
            continue

        slug = model.get("slug", "")
        if not slug:
            n_no_slug += 1
            continue

        title = model.get("title", slug.replace("-", " ").title())
        tags = model.get("tags", []) or []
        created_at = model.get("createdAt")
        image_rel = ((model.get("images") or {}).get("thumbnail")) or model.get("collectableImage") or ""
        thumbnail = f"https://assets.awwwards.com/awards/media/cache/thumb_440_330/{image_rel}" if image_rel else ""

        # Live URL + reconfirm slug via visit-count identifier
        live_url = ""
        live_matches = list(LIVE_URL_RE.finditer(card))
        if not live_matches and n_total <= 2:
            print(f"      [live miss] slug={slug} card_has_bt={'figure-rollover__bt' in card} len={len(card)}", file=sys.stderr)
            # Dump the card to disk for offline comparison
            dump = Path(__file__).with_name(f"_debug_card_{n_total}.html")
            dump.write_text(card, encoding="utf-8")
            print(f"      [live miss] dumped card to {dump}", file=sys.stderr)
        for lu in live_matches:
            if lu.group(2) == slug:
                live_url = lu.group(1)
                break
        if not live_url and live_matches:
            live_url = live_matches[0].group(1)

        # Agency (creator) info
        agency_m = AGENCY_RE.search(card)
        agency = agency_m.group(1).strip() if agency_m else ""
        agency_url_m = AGENCY_URL_RE.search(card)
        agency_url = (BASE + agency_url_m.group(1)) if agency_url_m and agency_url_m.group(1).startswith("/") else (agency_url_m.group(1) if agency_url_m else "")

        # SOTD award date
        ad_m = AWARD_DATE_RE.search(card)
        award_date = ad_m.group(1).strip() if ad_m else ""

        # Award tags (sotd / dev / hon / moty / etc.)
        award_tags = sorted({a.lower() for a in AWARD_TAGS_RE.findall(card)})

        yield {
            "slug": slug,
            "awwwards_url": f"{BASE}/sites/{slug}",
            "live_url": live_url,
            "title": title,
            "agency": agency,
            "agency_url": agency_url,
            "tags": tags,               # submitter-declared (e.g. "GSAP", "Three.js", ...)
            "award_tags": award_tags,   # awarded labels (sotd/dev/hon)
            "award_date": award_date,
            "created_at": created_at,
            "category": "SOTD",
            "thumbnail": thumbnail,
        }
    print(f"      [parse stats] total={n_total} no_model={n_no_model} bad_json={n_bad_json} no_slug={n_no_slug}", file=sys.stderr)


# --- Fallback: follow /sites/{slug} to resolve the live URL ------------------
# Used when the listing row doesn't have a direct figure-rollover__bt live link
# (rare — happens for some older entries). The detail page always has one.

DETAIL_LIVE_RE = re.compile(
    r'<a[^>]+class="[^"]*(?:btn-link-external|site-url|website-view)[^"]*"[^>]+href="(https?://[^"]+)"',
    re.IGNORECASE,
)
DETAIL_BLOCK_CTA_RE = re.compile(
    r'<a[^>]+data-event="site_click"[^>]+href="(https?://[^"]+)"',
    re.IGNORECASE,
)
DETAIL_DATA_HREF_RE = re.compile(
    r'data-(?:href|link)="(https?://[^"]+)"',
    re.IGNORECASE,
)


def resolve_live_url(awwwards_url: str) -> str:
    try:
        page = http_get(awwwards_url)
    except Exception as e:
        print(f"  [!] failed to fetch {awwwards_url}: {e}", file=sys.stderr)
        return ""

    for rx in (DETAIL_LIVE_RE, DETAIL_BLOCK_CTA_RE, DETAIL_DATA_HREF_RE):
        m = rx.search(page)
        if m and "awwwards.com" not in m.group(1):
            return m.group(1)
    return ""


# --- Main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100, help="Number of SOTD entries to collect")
    ap.add_argument("--offset", type=int, default=0, help="Skip N entries at start (for pagination)")
    ap.add_argument("--pages", type=int, default=15, help="Max listing pages to scan")
    ap.add_argument("--live", action="store_true", help="Also resolve live URLs (slower)")
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    print(f"Scraping up to {args.count} SOTD entries from {LISTING_URL}")
    print(f"Output: {args.output}")

    collected = []
    seen_slugs = set()

    for page in range(1, args.pages + 1):
        if len(collected) >= args.count + args.offset:
            break
        url = LISTING_URL if page == 1 else f"{LISTING_URL}?page={page}"
        print(f"  [page {page}] {url}")
        try:
            html = http_get(url)
        except Exception as e:
            print(f"    ERR: {e}")
            time.sleep(3)
            continue

        item_count = len(ITEM_RE.findall(html))
        print(f"    raw <li js-collectable> matches: {item_count}")
        items = list(parse_listing_page(html))
        print(f"    found {len(items)} items")
        if not items:
            # Listings page markup may have changed — dump a snippet for debugging
            debug = Path(__file__).with_name("_debug_last_page.html")
            debug.write_text(html, encoding="utf-8")
            print(f"    [warn] 0 items parsed. Dumped HTML to {debug}")
        for it in items:
            if it["slug"] in seen_slugs:
                continue
            seen_slugs.add(it["slug"])
            collected.append(it)
            if len(collected) >= args.count + args.offset:
                break
        time.sleep(1.5)  # polite

    collected = collected[args.offset:args.offset + args.count]
    print(f"\nCollected {len(collected)} listings (pre live-resolve)")

    if args.live:
        print("\nResolving live URLs...")
        for i, it in enumerate(collected, 1):
            if not it.get("live_url"):
                it["live_url"] = resolve_live_url(it["awwwards_url"])
            print(f"  [{i}/{len(collected)}] {it['slug']} -> {it.get('live_url') or '(none)'}")
            time.sleep(0.5)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for rank, it in enumerate(collected, 1):
            it["rank"] = rank
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    with_live = sum(1 for it in collected if it.get("live_url"))
    print(f"\nWrote {len(collected)} entries ({with_live} with live URLs) to {args.output}")


if __name__ == "__main__":
    main()
