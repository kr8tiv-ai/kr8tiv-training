"""Re-fetch titles for freefrontend records (the original scrape missed them)."""
import html
import json
import re
import time
import urllib.request
from pathlib import Path

JSONL = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'freefrontend-gsap.jsonl'
UA = 'Mozilla/5.0 Cipher/1.0'


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def title_from_detail(body):
    """Detail page has <h1 class="entry-title"> or similar."""
    patterns = [
        r'<h1[^>]*class="[^"]*entry-title[^"]*"[^>]*>([^<]+)</h1>',
        r'<h1[^>]*>([^<]+?)</h1>',
        r'<title>([^<]+?)(?:\s*\|\s*[^<]+)?</title>',
    ]
    for p in patterns:
        m = re.search(p, body)
        if m:
            return html.unescape(m.group(1).strip())
    return None


def main():
    records = [json.loads(l) for l in JSONL.read_text(encoding='utf-8').splitlines() if l.strip()]
    print(f'Fixing titles on {len(records)} records...', flush=True)

    updated = 0
    for i, rec in enumerate(records, 1):
        if rec.get('title') and rec['title'] != 'None':
            continue
        url = rec.get('detail_url')
        if not url:
            continue
        body = fetch(url)
        if not body:
            continue
        title = title_from_detail(body)
        if title:
            # Clean " | JavaScript" suffix
            title = re.sub(r'\s*\|\s*(JavaScript|CSS|HTML)\s*$', '', title)
            rec['title'] = title
            updated += 1
            print(f'[{i}/{len(records)}] {title}', flush=True)
        time.sleep(0.3)

    JSONL.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\n', encoding='utf-8')
    print(f'\nDONE. Updated {updated}/{len(records)} titles.', flush=True)


if __name__ == '__main__':
    main()
