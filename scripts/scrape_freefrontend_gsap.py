"""Scrape freefrontend.com/gsap-js/ pages 1-6 for real GSAP code.

Flow:
  1. Fetch each list page. Extract `.snippet-card` → title + detail URL + tech/difficulty/features.
  2. For each detail page, extract the CodePen URL.
  3. Fetch `https://cdpn.io/{user}/fullpage/{id}` → parse iframe srcdoc → real standalone HTML.
  4. Save as JSONL with full code + metadata.

Output: data/raw/freefrontend-gsap.jsonl
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Cipher/1.0'
BASE = 'https://freefrontend.com/gsap-js/'
OUT = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'freefrontend-gsap.jsonl'
OUT.parent.mkdir(parents=True, exist_ok=True)


def fetch(url: str, retries: int = 3, timeout: int = 25) -> str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,*/*'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode('utf-8', errors='replace')
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                print(f'   [fetch fail] {url}: {e}', flush=True)
                return None
            time.sleep(2 + attempt * 2)
    return None


def list_page_url(page: int) -> str:
    return BASE if page == 1 else f'{BASE}page/{page}/'


CARD_RE = re.compile(
    r'<div[^>]*class="[^"]*snippet-card[^"]*"[^>]*>(.+?)</div>\s*</div>',
    re.DOTALL | re.IGNORECASE,
)
TITLE_RE = re.compile(r'<h[123][^>]*>(.*?)</h[123]>', re.DOTALL)
LINK_RE = re.compile(r'<a\s+[^>]*href="(https://freefrontend\.com/code/[^"]+)"', re.DOTALL)
META_RE = re.compile(r'<div[^>]*class="[^"]*(?:features|tech|meta)[^"]*"[^>]*>(.+?)</div>', re.DOTALL)


def parse_list_cards(html_str: str) -> list[dict]:
    """Extract title + detail URL from list page snippet cards."""
    # Simple approach: find each detail URL and an <h> near it
    cards: list[dict] = []
    detail_urls = re.findall(r'href="(https://freefrontend\.com/code/[^"]+)"', html_str)
    seen: set[str] = set()
    for url in detail_urls:
        if url in seen:
            continue
        seen.add(url)
        # Find nearby title: scan forward 600 chars after the link
        idx = html_str.find(url)
        window = html_str[idx:idx + 1500]
        title_m = re.search(r'<h[123][^>]*>\s*<a[^>]*>([^<]+)</a>', window)
        if not title_m:
            title_m = re.search(r'<h[123][^>]*>([^<]+)</h[123]>', window)
        title = html.unescape(title_m.group(1).strip()) if title_m else None
        cards.append({'title': title, 'detail_url': url})
    return cards


PEN_RE = re.compile(r'https?://codepen\.io/([A-Za-z0-9_\-]+)/pen/([A-Za-z0-9_\-]+)')


def extract_pen_from_detail(detail_html: str) -> tuple[str, str] | None:
    m = PEN_RE.search(detail_html)
    if not m:
        return None
    return m.group(1), m.group(2)


SRCDOC_RE = re.compile(
    r'<iframe[^>]*\bsrcdoc="((?:[^"\\]|\\.)*)"',
    re.DOTALL,
)
SRCDOC_SINGLE_RE = re.compile(
    r"<iframe[^>]*\bsrcdoc='((?:[^'\\]|\\.)*)'",
    re.DOTALL,
)


def extract_pen_code(user: str, pen_id: str) -> str | None:
    url = f'https://cdpn.io/{user}/fullpage/{pen_id}'
    body = fetch(url)
    if not body:
        return None
    m = SRCDOC_RE.search(body) or SRCDOC_SINGLE_RE.search(body)
    if not m:
        return None
    return html.unescape(m.group(1))


def detail_meta(detail_html: str) -> dict:
    """Scrape tech list / difficulty / features from the detail page."""
    out = {}
    # Author
    author_m = re.search(r'<a[^>]*rel="author"[^>]*>([^<]+)</a>', detail_html)
    if author_m:
        out['author'] = html.unescape(author_m.group(1).strip())
    # Tags / tech stack (a .tags or .entry-tech section)
    tech_m = re.search(r'TECHNOLOGIES:?\s*</[^>]+>\s*<[^>]+>([^<]+)', detail_html)
    if tech_m:
        out['tech'] = html.unescape(tech_m.group(1)).strip()
    diff_m = re.search(r'DIFFICULTY:?\s*</[^>]+>\s*<[^>]+>([^<]+)', detail_html)
    if diff_m:
        out['difficulty'] = html.unescape(diff_m.group(1)).strip()
    return out


def main() -> None:
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    print(f'Scraping freefrontend.com/gsap-js pages 1..{pages}', flush=True)

    all_cards: list[dict] = []
    for p in range(1, pages + 1):
        url = list_page_url(p)
        print(f'[page {p}] {url}', flush=True)
        body = fetch(url)
        if not body:
            print(f'   skip — fetch failed', flush=True)
            continue
        cards = parse_list_cards(body)
        print(f'   {len(cards)} cards found', flush=True)
        for c in cards:
            c['list_page'] = p
        all_cards.extend(cards)
        time.sleep(1.2)

    # De-dupe by detail_url
    seen: set[str] = set()
    unique: list[dict] = []
    for c in all_cards:
        if c['detail_url'] in seen:
            continue
        seen.add(c['detail_url'])
        unique.append(c)
    print(f'TOTAL unique cards: {len(unique)}', flush=True)

    count_with_code = 0
    with OUT.open('w', encoding='utf-8') as f:
        for i, card in enumerate(unique, 1):
            print(f'[{i}/{len(unique)}] {card["title"]}', flush=True)
            detail_body = fetch(card['detail_url'])
            if not detail_body:
                continue
            pen = extract_pen_from_detail(detail_body)
            meta = detail_meta(detail_body)
            if not pen:
                record = {**card, **meta, 'pen_user': None, 'pen_id': None, 'code_html': None}
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                continue
            user, pen_id = pen
            code = extract_pen_code(user, pen_id)
            record = {
                **card,
                **meta,
                'pen_user': user,
                'pen_id': pen_id,
                'pen_url': f'https://codepen.io/{user}/pen/{pen_id}',
                'code_html': code,
                'code_length': len(code) if code else 0,
            }
            if code:
                count_with_code += 1
                print(f'   OK pen={user}/{pen_id} code_len={len(code):,}', flush=True)
            else:
                print(f'   skip — no pen code for {user}/{pen_id}', flush=True)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            f.flush()
            time.sleep(0.8)

    print(f'\nDONE. {count_with_code}/{len(unique)} entries captured real code.', flush=True)
    print(f'Output: {OUT}', flush=True)


if __name__ == '__main__':
    main()
