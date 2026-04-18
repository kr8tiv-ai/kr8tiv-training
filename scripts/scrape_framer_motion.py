"""Scrape real Framer Motion examples from the official motion (framer-motion) repo.

Strategy: the `motion/motion` repo on GitHub has a `dev/` directory with runnable
React examples using every feature of the library. We pull each .tsx/.jsx file.

We also pull from `motion.dev/examples` mdx docs which embed real code blocks.
"""
import base64
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'raw' / 'framer-motion.jsonl'
OUT.parent.mkdir(parents=True, exist_ok=True)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Cipher/1.0'
GH_API = 'https://api.github.com'


def fetch(url, headers=None, retries=2):
    hdrs = {'User-Agent': UA, 'Accept': 'application/vnd.github.v3+json'}
    if headers: hdrs.update(headers)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Rate limit — back off
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


def walk_repo_dir(owner, repo, path, branch='main'):
    """List files under a repo dir using GitHub contents API."""
    url = f'{GH_API}/repos/{owner}/{repo}/contents/{path}?ref={branch}'
    body = fetch(url)
    if not body:
        return []
    try:
        data = json.loads(body)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    files = []
    for item in data:
        if item['type'] == 'file':
            files.append({'path': item['path'], 'download_url': item['download_url'], 'size': item['size']})
        elif item['type'] == 'dir':
            files.extend(walk_repo_dir(owner, repo, item['path'], branch))
        time.sleep(0.1)
    return files


def scrape_motion_dev_repo():
    """Pull Framer Motion dev playground examples from motiondivision/motion."""
    # Current canonical motion repo
    owner, repo = 'motiondivision', 'motion'
    dev_dirs = ['dev/react/src/examples']  # main example source

    all_files = []
    for d in dev_dirs:
        print(f'[fm] walking {owner}/{repo}/{d}', flush=True)
        files = walk_repo_dir(owner, repo, d)
        print(f'[fm] {d}: {len(files)} files', flush=True)
        all_files.extend(files)
        if len(all_files) >= 200:
            break

    records = []
    for i, f in enumerate(all_files, 1):
        if not f['path'].endswith(('.tsx', '.jsx', '.ts', '.js', '.html', '.mdx')):
            continue
        if f['size'] > 200000:
            continue
        code = fetch(f['download_url'])
        if not code or len(code) < 100:
            continue
        has_motion = 'motion.' in code or "from 'motion'" in code or 'from "motion"' in code or 'framer-motion' in code
        records.append({
            'source': 'framer-motion-repo',
            'repo': f'{owner}/{repo}',
            'path': f['path'],
            'raw_url': f['download_url'],
            'size': f['size'],
            'code': code,
            'has_motion_usage': has_motion,
        })
        if i % 20 == 0:
            print(f'[fm] {i}/{len(all_files)} files captured', flush=True)
        time.sleep(0.2)
    return records


def main():
    print('Scraping Framer Motion real examples...', flush=True)
    records = scrape_motion_dev_repo()
    print(f'Total: {len(records)} records', flush=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'Written to {OUT}', flush=True)
    # Audit
    with_motion = sum(1 for r in records if r['has_motion_usage'])
    sizes = [r['size'] for r in records]
    if sizes:
        print(f'  Size: min={min(sizes)} max={max(sizes)} mean={sum(sizes)//len(sizes)}')
    print(f'  Has motion usage: {with_motion}/{len(records)}')


if __name__ == '__main__':
    main()
