"""Build SFT training JSONL from the 4 real scraped sources.

Output: data/prompts/cipher-real-v1-sft.jsonl
Format: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}

Rules for building:
  - Every assistant response is REAL scraped code (no templates)
  - Prompts are derived from record metadata (title, description, tags)
  - Filter out junk: empty, too small, broken HTML
  - Per-source caps so no source dominates
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'prompts' / 'cipher-real-v1-sft.jsonl'
OUT.parent.mkdir(parents=True, exist_ok=True)

random.seed(42)

SYSTEM = (
    "You are Cipher, the Code Kraken. Build COMPLETE Awwwards-quality code from the brief.\n"
    "Output ONLY code — no preamble, no fences. Match the style + motion stack of the brief."
)


def from_gsap():
    p = RAW / 'freefrontend-gsap.jsonl'
    records = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    out = []
    for r in records:
        code = r.get('code_html')
        if not code or len(code) < 1500:
            continue
        # Must be real HTML
        if '<!DOCTYPE' not in code.upper() and '<html' not in code.lower():
            continue
        title = r.get('title') or 'a GSAP animation'
        tech = r.get('tech', '')
        feats = r.get('features', '')
        user = f"Build a single-file HTML page demonstrating \"{title}\". Use GSAP. {tech}. {feats}".strip()
        out.append({
            'source': 'gsap-freefrontend',
            'messages': [
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': code},
            ],
        })
    return out


def from_threejs():
    p = RAW / 'threejs-examples.jsonl'
    records = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    out = []
    for r in records:
        code = r.get('code')
        if not code or len(code) < 1500:
            continue
        if '<html' not in code.lower():
            continue
        name = r.get('name', 'three.js demo').replace('_', ' ')
        # Classify by name prefix
        kind = 'WebGL' if name.startswith('webgl') else ('CSS3D' if name.startswith('css3d') else 'Three.js')
        user = f"Build a single-file HTML {kind} demo: \"{name}\" using three.js. Include all scripts, shaders, and geometry inline."
        out.append({
            'source': 'threejs-official',
            'messages': [
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': code},
            ],
        })
    return out


def from_framer_motion():
    p = RAW / 'framer-motion.jsonl'
    records = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    out = []
    for r in records:
        code = r.get('code')
        if not code or len(code) < 150:
            continue
        # Derive a brief from the path
        path = r.get('path', '')
        fname = Path(path).stem if path else 'demo'
        # AnimatePresence-image-gallery -> Animate Presence image gallery
        readable = re.sub(r'[_\-]+', ' ', fname).strip()
        user = f"Build a React TSX component demonstrating \"{readable}\" using framer-motion. Include full imports."
        out.append({
            'source': 'framer-motion-official',
            'messages': [
                {'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': code},
            ],
        })
    return out


def from_aura_shells():
    """Use shells as REFERENCE prompts — no full HTML, but real briefs with preview images."""
    p = RAW / 'aura-templates-shells.jsonl'
    records = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    out = []
    for r in records[:500]:  # cap at 500 to avoid dominating
        if r.get('status') != 200:
            continue
        title = r.get('title')
        desc = r.get('description')
        if not title or not desc:
            continue
        # These don't have full HTML, so they become PROMPT-only training
        # signals. Skip for SFT and use them only in a separate "reference
        # catalog" so Cipher learns the BRAND of each template without
        # memorizing fake HTML.
        continue
    return out


def main():
    gsap_rows = from_gsap()
    three_rows = from_threejs()
    fm_rows = from_framer_motion()
    aura_rows = from_aura_shells()

    print(f'gsap_rows: {len(gsap_rows)}')
    print(f'three_rows: {len(three_rows)}')
    print(f'fm_rows: {len(fm_rows)}')
    print(f'aura_rows: {len(aura_rows)}')

    all_rows = gsap_rows + three_rows + fm_rows + aura_rows
    random.shuffle(all_rows)

    with OUT.open('w', encoding='utf-8') as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f'\nTotal: {len(all_rows)} training records')
    print(f'Output: {OUT}')
    print(f'Size: {OUT.stat().st_size / 1024 / 1024:.2f} MB')


if __name__ == '__main__':
    main()
