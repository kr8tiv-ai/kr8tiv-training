"""Scrape real Three.js examples from the official mrdoob/three.js repo.

The examples/ directory of the three.js repo contains ~300 standalone HTML
files, each a self-contained WebGL demo. Every one is a real renderable
single-file HTML page with imports, uniforms, shaders, and geometry setup.

This is exactly the kind of "Awwwards creative code" training data we want.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'raw' / 'threejs-examples.jsonl'
OUT.parent.mkdir(parents=True, exist_ok=True)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Cipher/1.0'
GH_API = 'https://api.github.com'
RAW_BASE = 'https://raw.githubusercontent.com/mrdoob/three.js/dev'


def fetch(url, retries=2):
    hdrs = {'User-Agent': UA, 'Accept': 'application/vnd.github.v3+json'}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code == 403:
                time.sleep(30)
            elif attempt == retries - 1:
                return None
            else:
                time.sleep(2)
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2)
    return None


def list_examples():
    """Fetch the examples directory tree."""
    url = f'{GH_API}/repos/mrdoob/three.js/contents/examples?ref=dev'
    body = fetch(url)
    if not body:
        return []
    items = json.loads(body)
    # We want .html files at top level (webgl_*.html, etc.)
    return [i for i in items if i['type'] == 'file' and i['name'].endswith('.html')]


def main():
    print('Scraping three.js examples...', flush=True)
    items = list_examples()
    print(f'Found {len(items)} .html examples', flush=True)

    records = []
    for i, item in enumerate(items, 1):
        if item['size'] > 250000:
            continue
        code = fetch(item['download_url'])
        if not code or '<html' not in code.lower():
            continue
        has_three = 'THREE.' in code or "from 'three'" in code or 'import * as THREE' in code
        has_webgl = 'gl_FragColor' in code or 'WebGLRenderer' in code or 'ShaderMaterial' in code
        records.append({
            'source': 'threejs-official',
            'name': item['name'].replace('.html', ''),
            'path': item['path'],
            'raw_url': item['download_url'],
            'size': item['size'],
            'code': code,
            'has_three': has_three,
            'has_webgl': has_webgl,
        })
        if i % 20 == 0:
            print(f'[three] {i}/{len(items)} captured', flush=True)
        time.sleep(0.15)

    with OUT.open('w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'Total: {len(records)} records', flush=True)
    print(f'Written to {OUT}', flush=True)

    with_three = sum(1 for r in records if r['has_three'])
    with_webgl = sum(1 for r in records if r['has_webgl'])
    sizes = [r['size'] for r in records]
    if sizes:
        print(f'  Size: min={min(sizes)} max={max(sizes)} mean={sum(sizes)//len(sizes)}')
    print(f'  Has THREE. usage: {with_three}/{len(records)}')
    print(f'  Has WebGL/shader: {with_webgl}/{len(records)}')


if __name__ == '__main__':
    main()
