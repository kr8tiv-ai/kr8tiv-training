"""Parse aura.build/sitemap.xml and classify template URLs by type.
Writes all template URLs to data/raw/aura-templates.txt for scraping.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / 'data' / 'raw'
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = 'https://www.aura.build/sitemap.xml'
UA = 'Mozilla/5.0 Cipher/1.0'


def fetch(u):
    req = urllib.request.Request(u, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace')


def main():
    print(f'Fetching {URL}...', flush=True)
    body = fetch(URL)
    locs = re.findall(r'<loc>([^<]+)</loc>', body)
    print(f'Total URLs: {len(locs)}', flush=True)

    buckets: dict[str, list[str]] = {}
    for loc in locs:
        m = re.match(r'https?://(?:www\.)?aura\.build/([a-z\-]+)', loc)
        key = m.group(1) if m else '(root)'
        buckets.setdefault(key, []).append(loc)

    print('\nURL path segments:')
    for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        print(f'  /{k}: {len(v)}', flush=True)

    # Templates are at /templates/{slug}
    templates = [loc for loc in locs if '/templates/' in loc]
    components = [loc for loc in locs if '/components/' in loc]
    print(f'\nTemplates: {len(templates)}')
    print(f'Components: {len(components)}')

    (OUT_DIR / 'aura-template-urls.txt').write_text('\n'.join(templates), encoding='utf-8')
    (OUT_DIR / 'aura-component-urls.txt').write_text('\n'.join(components), encoding='utf-8')
    print(f'\nWritten: {OUT_DIR}/aura-template-urls.txt ({len(templates)})')
    print(f'Written: {OUT_DIR}/aura-component-urls.txt ({len(components)})')

    # Sample
    print('\nFirst 5 templates:')
    for u in templates[:5]: print(f'  {u}')


if __name__ == '__main__':
    main()
