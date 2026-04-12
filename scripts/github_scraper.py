#!/usr/bin/env python3
"""
GitHub Creative Code Scraper for Cipher Code Kraken Training Data.

Discovers repos by creative-dev topics (awwwards, GSAP, Three.js, Lenis, etc.),
clones them shallow, extracts JS/TS/CSS files containing creative patterns,
and outputs structured JSONL for the training pipeline.

Usage:
    python scripts/github_scraper.py --github-token ghp_xxx --output data/raw/github.jsonl
    python scripts/github_scraper.py --output data/raw/github.jsonl --max-repos 50
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from github import Github, RateLimitExceededException

# ─── Configuration ────────────────────────────────────────────────────────────

CREATIVE_TOPICS = [
    "awwwards",
    "awwwards-inspired",
    "gsap-scrolltrigger",
    "gsap-animation",
    "threejs",
    "lenis-scroll",
    "animated-website",
]

# Files must contain at least one of these creative signals to be included
CREATIVE_SIGNALS = [
    "three",
    "THREE",
    "gsap",
    "ScrollTrigger",
    "Lenis",
    "requestAnimationFrame",
    "gl_FragColor",
    "shader",
    "canvas",
    "WebGL",
    "clip-path",
    "mix-blend-mode",
]

# File extensions to extract
TARGET_EXTENSIONS = {".js", ".ts", ".jsx", ".tsx", ".css"}

# Minimum star count for quality filtering
MIN_STARS = 10

# Minimum line count -- skip trivially short files
MIN_LINES = 20

# Maximum average line length before considering file minified
MAX_AVG_LINE_LENGTH = 200


# ─── Helpers ──────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    """Log progress to stderr so stdout stays clean for JSONL."""
    print(msg, file=sys.stderr, flush=True)


def is_minified(filepath: str, content: str) -> bool:
    """Detect minified files by filename or average line length."""
    if ".min." in os.path.basename(filepath):
        return True
    lines = content.split("\n")
    if not lines:
        return True
    avg_len = sum(len(line) for line in lines) / len(lines)
    return avg_len > MAX_AVG_LINE_LENGTH


def has_creative_signal(content: str) -> bool:
    """Check if file content contains at least one creative code signal."""
    for signal in CREATIVE_SIGNALS:
        if signal in content:
            return True
    return False


def line_count(content: str) -> int:
    """Count non-empty lines."""
    return len([line for line in content.split("\n") if line.strip()])


def extract_license(repo) -> str:
    """Extract license name from repo, or 'unknown'."""
    try:
        lic = repo.get_license()
        return lic.license.spdx_id if lic and lic.license else "unknown"
    except Exception:
        return "unknown"


# ─── Core Scraping ────────────────────────────────────────────────────────────


def discover_repos(gh: Github, max_repos: int) -> list:
    """
    Search GitHub for repos matching creative-dev topics.
    Deduplicates across topics. Filters by minimum stars.
    """
    seen_repos = set()
    repos = []

    for topic in CREATIVE_TOPICS:
        log(f"[discover] Searching topic: {topic}")
        query = f"topic:{topic} stars:>{MIN_STARS}"
        try:
            results = gh.search_repositories(query=query, sort="stars", order="desc")
            count = 0
            for repo in results:
                if repo.full_name in seen_repos:
                    continue
                seen_repos.add(repo.full_name)
                repos.append(repo)
                count += 1
                if len(repos) >= max_repos:
                    log(f"[discover] Reached max_repos limit ({max_repos})")
                    return repos
            log(f"[discover] Found {count} new repos for topic '{topic}' (total: {len(repos)})")
        except RateLimitExceededException:
            log("[discover] Rate limit hit -- stopping discovery early")
            break
        except Exception as e:
            log(f"[discover] Error searching topic '{topic}': {e}")
            continue

    log(f"[discover] Total unique repos discovered: {len(repos)}")
    return repos


def clone_repo(repo_url: str, dest: str) -> bool:
    """Shallow clone a repo. Returns True on success."""
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, dest],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return os.path.isdir(dest)
    except Exception as e:
        log(f"[clone] Failed: {e}")
        return False


def extract_creative_files(repo_dir: str) -> list[dict]:
    """
    Walk a cloned repo and extract files matching creative signals.
    Returns list of {"file": relative_path, "content": str}.
    """
    extracted = []
    repo_path = Path(repo_dir)

    for root, _dirs, files in os.walk(repo_path):
        # Skip node_modules, dist, build, .git, vendor
        rel_root = os.path.relpath(root, repo_dir)
        skip_dirs = {"node_modules", "dist", "build", ".git", "vendor", ".next", "__pycache__"}
        if any(part in skip_dirs for part in Path(rel_root).parts):
            continue

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in TARGET_EXTENSIONS:
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, repo_dir)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            # Filter: skip minified
            if is_minified(rel_path, content):
                continue

            # Filter: skip short files
            if line_count(content) < MIN_LINES:
                continue

            # Filter: must contain creative signal
            if not has_creative_signal(content):
                continue

            extracted.append({"file": rel_path, "content": content})

    return extracted


def scrape_repos(gh: Github, max_repos: int, output_path: str) -> None:
    """
    Main scraping pipeline: discover repos, clone, extract, output JSONL.
    """
    repos = discover_repos(gh, max_repos)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    total_files = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for i, repo in enumerate(repos):
            log(f"[scrape] ({i + 1}/{len(repos)}) Processing {repo.full_name} ({repo.stargazers_count} stars)")

            # Get license
            license_id = extract_license(repo)
            topics = repo.get_topics() if hasattr(repo, "get_topics") else []

            # Clone to temp directory
            tmp_dir = tempfile.mkdtemp(prefix="cipher_scrape_")
            try:
                clone_url = repo.clone_url
                if not clone_repo(clone_url, os.path.join(tmp_dir, "repo")):
                    log(f"[scrape] Failed to clone {repo.full_name}, skipping")
                    continue

                # Extract creative files
                files = extract_creative_files(os.path.join(tmp_dir, "repo"))
                log(f"[scrape] Extracted {len(files)} creative files from {repo.full_name}")

                for file_entry in files:
                    record = {
                        "source": "github",
                        "repo": repo.full_name,
                        "file": file_entry["file"],
                        "content": file_entry["content"],
                        "license": license_id,
                        "stars": repo.stargazers_count,
                        "topics": list(topics),
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    total_files += 1

            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    log(f"[scrape] Complete. {total_files} files written to {output_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape creative code from GitHub repos for Cipher training data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/github_scraper.py --github-token ghp_xxx --output data/raw/github.jsonl
  python scripts/github_scraper.py --output data/raw/github.jsonl --max-repos 50

Topics searched: awwwards, awwwards-inspired, gsap-scrolltrigger, gsap-animation,
                 threejs, lenis-scroll, animated-website

Output format (JSONL):
  {"source": "github", "repo": "owner/name", "file": "path", "content": "...",
   "license": "MIT", "stars": 42, "topics": [...]}
        """,
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var). "
        "Authenticated: 5000 req/hr. Unauthenticated: 60 req/hr.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file path for JSONL data (e.g., data/raw/github.jsonl)",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=500,
        help="Maximum number of repos to process (default: 500)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Initialize GitHub client
    gh = Github(args.github_token) if args.github_token else Github()

    if args.github_token:
        log("[init] Authenticated GitHub client (5000 req/hr)")
    else:
        log("[init] Unauthenticated GitHub client (60 req/hr) -- pass --github-token for higher limits")

    scrape_repos(gh, args.max_repos, args.output)


if __name__ == "__main__":
    main()
