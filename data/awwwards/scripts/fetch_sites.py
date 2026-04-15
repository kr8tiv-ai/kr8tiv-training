"""Fetch live HTML for each Awwwards SOTD winner in listings.jsonl.

Writes to data/awwwards/raw/{slug}/index.html + metadata.json.

Uses a browser UA and parallel workers. Skips sites already fetched.
Resolves and fetches linked stylesheets (up to 3 per site) into styles/.

Usage:
    python fetch_sites.py [--concurrency 6] [--refetch]
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent            # data/awwwards/
LISTINGS = ROOT / "listings.jsonl"
RAW = ROOT / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def http_get(url: str, timeout: int = 30, max_bytes: int = 5_000_000) -> tuple[int, str, str]:
    """Return (status, content_type, text)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,text/css,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ctype = r.headers.get("Content-Type", "")
            raw = r.read(max_bytes)
            status = r.status
    except Exception as e:
        return 0, "", f"__ERROR__: {type(e).__name__}: {e}"

    # Best-effort decode
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return status, ctype, raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return status, ctype, raw.decode("utf-8", errors="replace")


STYLESHEET_RE = re.compile(
    r'<link[^>]+rel=["\']?stylesheet["\']?[^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
STYLESHEET_RE2 = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']?stylesheet["\']?',
    re.IGNORECASE,
)


def extract_stylesheets(html: str, base_url: str, limit: int = 3) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for rx in (STYLESHEET_RE, STYLESHEET_RE2):
        for m in rx.finditer(html):
            href = m.group(1).strip()
            if not href or href.startswith("data:"):
                continue
            full = urllib.parse.urljoin(base_url, href)
            if full in seen:
                continue
            seen.add(full)
            out.append(full)
            if len(out) >= limit:
                return out
    return out


def fetch_one(entry: dict, refetch: bool) -> dict:
    slug = entry["slug"]
    live_url = entry.get("live_url") or ""
    out_dir = RAW / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    idx_path = out_dir / "index.html"
    meta_path = out_dir / "metadata.json"

    result = {
        "slug": slug,
        "live_url": live_url,
        "status": None,
        "bytes": 0,
        "css_count": 0,
        "error": None,
    }

    if not live_url:
        result["error"] = "no_live_url"
        return result

    if idx_path.exists() and not refetch:
        result["status"] = 200
        result["bytes"] = idx_path.stat().st_size
        # Best-effort CSS count
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            result["css_count"] = len(meta.get("stylesheets", []))
        except Exception:
            pass
        result["error"] = "cached"
        return result

    # Fetch HTML
    status, ctype, body = http_get(live_url)
    if status == 0:
        result["error"] = body[:200]
        return result
    if status >= 400:
        result["status"] = status
        result["error"] = f"http_{status}"
        return result

    result["status"] = status
    idx_path.write_text(body, encoding="utf-8")
    result["bytes"] = len(body.encode("utf-8", errors="ignore"))

    # Extract + fetch first 3 stylesheets
    sheets = extract_stylesheets(body, live_url, limit=3)
    styles_dir = out_dir / "styles"
    styles_dir.mkdir(exist_ok=True)
    fetched_sheets: list[dict] = []
    for i, sheet_url in enumerate(sheets):
        s_status, s_ctype, s_body = http_get(sheet_url, timeout=15, max_bytes=1_000_000)
        if s_status == 0 or s_status >= 400:
            fetched_sheets.append({"url": sheet_url, "status": s_status, "error": s_body[:120] if s_status == 0 else f"http_{s_status}"})
            continue
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", urllib.parse.urlsplit(sheet_url).path)[-80:] or f"stylesheet_{i}.css"
        if not safe.endswith(".css"):
            safe += ".css"
        (styles_dir / safe).write_text(s_body, encoding="utf-8", errors="ignore")
        fetched_sheets.append({"url": sheet_url, "status": s_status, "file": safe, "bytes": len(s_body)})

    result["css_count"] = len(fetched_sheets)

    meta = {
        **{k: v for k, v in entry.items() if k not in ("__local__",)},
        "fetched_at": int(time.time()),
        "content_type": ctype,
        "http_status": status,
        "html_bytes": result["bytes"],
        "stylesheets": fetched_sheets,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Only process first N entries (0=all)")
    args = ap.parse_args()

    if not LISTINGS.exists():
        print(f"[err] {LISTINGS} missing. Run scrape_listings.py first.", file=sys.stderr)
        sys.exit(1)

    entries = [json.loads(line) for line in LISTINGS.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        entries = entries[:args.limit]
    print(f"Fetching {len(entries)} sites with concurrency={args.concurrency} refetch={args.refetch}")

    ok = err = cached = 0
    with cf.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(fetch_one, e, args.refetch): e for e in entries}
        for i, f in enumerate(cf.as_completed(futures), 1):
            e = futures[f]
            try:
                r = f.result()
            except Exception as exc:
                r = {"slug": e["slug"], "error": f"exc:{exc}"}
            if r.get("error") == "cached":
                cached += 1
                state = "CACHED"
            elif r.get("error"):
                err += 1
                state = f"ERR: {r['error']}"
            else:
                ok += 1
                state = f"OK {r.get('bytes',0)/1024:.1f}KB css={r.get('css_count', 0)}"
            print(f"  [{i:3d}/{len(entries)}] {r['slug']:<45} {state}")

    print(f"\nDone. ok={ok} cached={cached} err={err}")


if __name__ == "__main__":
    main()
