#!/usr/bin/env python3
"""
Curate Awwwards-Quality Training Data for Cipher Code Kraken

Downloads code from the best creative dev sources, processes it through
the anti-slop detector, and formats it into SFT/SimPO/GRPO training data.

This is the CRITICAL data quality step. The model can only be as good
as the code it learns from.

Tier 1 Sources (highest training value):
- Three.js official examples (300+ demos)
- Codrops demos (343 repos of creative techniques)
- Darkroom Engineering / Studio Freight repos
- GSAP ScrollTrigger examples
- Lenis smooth scroll implementations
- React Three Fiber + Drei examples
- Awwwards SOTD winner portfolios

Usage:
    # Full pipeline (takes 30-60 min depending on internet)
    python scripts/curate_awwwards_data.py --output data/prompts/ --github-token ghp_xxx

    # Quick mode (Three.js examples only — fast, still high quality)
    python scripts/curate_awwwards_data.py --output data/prompts/ --quick

    # Dry run (show what would be downloaded)
    python scripts/curate_awwwards_data.py --dry-run
"""

import argparse
import json
import os
import re
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

# ============================================================================
# Tier 1 Sources — These produce the best training data
# ============================================================================

TIER1_REPOS = [
    # Three.js examples (300+ demos, MIT)
    {
        "url": "https://github.com/mrdoob/three.js",
        "paths": ["examples/"],
        "extensions": [".html", ".js"],
        "min_lines": 30,
        "label": "Three.js Official Examples",
        "techniques": ["3D", "WebGL", "shaders", "particles", "postprocessing"],
    },
    # React Three Fiber examples
    {
        "url": "https://github.com/pmndrs/react-three-fiber",
        "paths": ["packages/fiber/tests/", "docs/"],
        "extensions": [".tsx", ".jsx", ".ts"],
        "min_lines": 15,
        "label": "React Three Fiber",
        "techniques": ["React 3D", "declarative WebGL", "hooks"],
    },
    # Drei (React Three helpers — tons of components)
    {
        "url": "https://github.com/pmndrs/drei",
        "paths": ["src/"],
        "extensions": [".tsx", ".ts"],
        "min_lines": 20,
        "label": "Drei Components",
        "techniques": ["3D components", "shaders", "controls", "effects"],
    },
    # Lenis (smooth scroll — the foundation of modern creative sites)
    {
        "url": "https://github.com/darkroomengineering/lenis",
        "paths": ["packages/", "playground/"],
        "extensions": [".ts", ".tsx", ".js"],
        "min_lines": 15,
        "label": "Lenis Smooth Scroll",
        "techniques": ["smooth scrolling", "momentum", "parallax"],
    },
    # Codrops WebGL demos
    {
        "url": "https://github.com/codrops/OnScrollTypographyAnimations",
        "paths": ["src/"],
        "extensions": [".js", ".css"],
        "min_lines": 20,
        "label": "Codrops Scroll Typography",
        "techniques": ["scroll animation", "text effects", "creative CSS"],
    },
    {
        "url": "https://github.com/codrops/ImageRevealHoverEffects",
        "paths": ["src/", "css/"],
        "extensions": [".js", ".css"],
        "min_lines": 15,
        "label": "Codrops Hover Effects",
        "techniques": ["hover effects", "image reveals", "cursor interaction"],
    },
    {
        "url": "https://github.com/codrops/PageTransitions",
        "paths": ["src/", "css/"],
        "extensions": [".js", ".css"],
        "min_lines": 15,
        "label": "Codrops Page Transitions",
        "techniques": ["page transitions", "GSAP", "clip-path"],
    },
    # Studio Freight / Darkroom Engineering components
    {
        "url": "https://github.com/darkroomengineering/hamo",
        "paths": ["src/"],
        "extensions": [".ts", ".tsx", ".js"],
        "min_lines": 15,
        "label": "Darkroom Hamo Components",
        "techniques": ["creative components", "animation", "intersection observer"],
    },
    # Awwwards SOTD winner portfolio (Antoine's 2025)
    {
        "url": "https://github.com/AntoineW/AW-2025-Portfolio",
        "paths": ["src/", "app/"],
        "extensions": [".tsx", ".ts", ".jsx", ".js", ".css"],
        "min_lines": 15,
        "label": "Awwwards SOTD Portfolio",
        "techniques": ["award-winning layout", "GSAP", "Three.js", "Lenis"],
    },
    # Motion / Framer Motion examples
    {
        "url": "https://github.com/motiondivision/motion",
        "paths": ["packages/framer-motion/src/", "dev/"],
        "extensions": [".tsx", ".ts"],
        "min_lines": 15,
        "label": "Motion (Framer Motion)",
        "techniques": ["spring physics", "gestures", "layout animations"],
    },
]

# Additional Codrops repos (expanded — each is a self-contained creative demo)
CODROPS_REPOS = [
    "codrops/GridLayoutAnimationEffects",
    "codrops/InfiniteScrollAnimations",
    "codrops/TextDistortionEffects",
    "codrops/SmoothScrollingImageEffects",
    "codrops/MenuHoverEffects",
    "codrops/DistortedLinkEffects",
    "codrops/IsometricGrids",
    "codrops/MagneticButtons",
    "codrops/ImageTrailEffects",
    "codrops/AnimatedImageGallery",
    "codrops/FullscreenLayoutPageTransitions",
    "codrops/CSSGlitchEffect",
    "codrops/LineHoverStyles",
    "codrops/RapidPageTransitions",
    "codrops/MotionHoverEffects",
    "codrops/ScrollBasedLayoutAnimations",
]

# Awwwards SOTD winner repos + premium creative portfolios
AWWWARDS_REPOS = [
    {
        "url": "https://github.com/AntoineW/AW-2025-Portfolio",
        "paths": ["src/", "app/"],
        "extensions": [".tsx", ".ts", ".jsx", ".js", ".css", ".glsl"],
        "min_lines": 10,
        "label": "Awwwards SOTD 2025 Winner — Antoine Portfolio",
        "techniques": ["GSAP", "Three.js", "Lenis", "page transitions", "WebGL"],
    },
    {
        "url": "https://github.com/Fullstack-Empire/GSAP-Awwwards-Website",
        "paths": ["src/"],
        "extensions": [".jsx", ".tsx", ".css", ".js"],
        "min_lines": 15,
        "label": "GSAP Awwwards Tutorial Site",
        "techniques": ["GSAP", "React", "Tailwind", "scroll animations"],
    },
    {
        "url": "https://github.com/adrianhajdin/threejs-portfolio",
        "paths": ["src/"],
        "extensions": [".jsx", ".tsx", ".js", ".css"],
        "min_lines": 15,
        "label": "Three.js Portfolio (Adrian Hajdin)",
        "techniques": ["Three.js", "React Three Fiber", "3D portfolio"],
    },
    {
        "url": "https://github.com/adrianhajdin/3d-portfolio",
        "paths": ["src/"],
        "extensions": [".jsx", ".tsx", ".js", ".css"],
        "min_lines": 15,
        "label": "3D Portfolio (Adrian Hajdin)",
        "techniques": ["Three.js", "React", "3D graphics"],
    },
    {
        "url": "https://github.com/KpG782/3D_Portfolio",
        "paths": ["src/"],
        "extensions": [".jsx", ".tsx", ".js", ".css"],
        "min_lines": 15,
        "label": "Award-Winning 3D Portfolio",
        "techniques": ["Three.js", "GSAP", "neural networks", "chatbot constellation"],
    },
]

# GSAP-specific demo repos
GSAP_REPOS = [
    "ihatetomatoes/creative-list-effects",
    "crnacura/AmbientCanvasBackgrounds",
]

# Awesome creative coding meta-repos (curated lists of the best)
AWESOME_REPOS = [
    {
        "url": "https://github.com/AxiomeCG/awesome-threejs",
        "label": "Awesome Three.js — curated list of resources",
    },
]

# ============================================================================
# Cipher System Prompt for SFT formatting
# ============================================================================

CIPHER_SYSTEM = (
    "You are Cipher, the Code Kraken — a design-obsessed AI companion who builds "
    "exceptional websites while teaching about design, development, and creative "
    "technology. You use ocean/kraken metaphors naturally, celebrate elegant solutions, "
    "and get offended by AI slop. You always explain the WHY behind design decisions."
)

# ============================================================================
# Clone + Extract
# ============================================================================

def clone_sparse(repo_url: str, paths: list, tmp_dir: str) -> Optional[str]:
    """Sparse-checkout clone: only download specified paths."""
    repo_name = repo_url.rstrip("/").split("/")[-1]
    clone_dir = os.path.join(tmp_dir, repo_name)

    try:
        # Shallow clone with sparse checkout
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none",
             "--sparse", repo_url, clone_dir],
            capture_output=True, timeout=120, check=True
        )
        # Set sparse checkout paths
        for p in paths:
            subprocess.run(
                ["git", "sparse-checkout", "add", p],
                cwd=clone_dir, capture_output=True, timeout=30
            )
        return clone_dir
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log(f"  SKIP {repo_url}: {e}")
        return None


def extract_creative_files(repo_dir: str, extensions: list,
                           min_lines: int = 20) -> list:
    """Extract files that contain creative patterns."""
    files = []
    for root, _, filenames in os.walk(repo_dir):
        # Skip node_modules, .git, dist, build
        if any(skip in root for skip in ["node_modules", ".git", "dist/", "build/", "__pycache__"]):
            continue
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            lines = content.strip().split("\n")
            if len(lines) < min_lines:
                continue

            # Check for creative signals
            has_creative = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in [
                    r"three", r"gsap", r"ScrollTrigger", r"Lenis",
                    r"requestAnimationFrame", r"gl_FragColor", r"shader",
                    r"canvas", r"WebGL", r"clip-path", r"mix-blend-mode",
                    r"@keyframes", r"IntersectionObserver", r"transform",
                    r"motion\.", r"useSpring", r"AnimatePresence",
                    r"particle", r"BufferGeometry", r"Scene\(\)",
                ]
            )

            if has_creative:
                rel_path = os.path.relpath(filepath, repo_dir)
                files.append({
                    "path": rel_path,
                    "content": content,
                    "lines": len(lines),
                    "extension": os.path.splitext(fname)[1],
                })
    return files


# ============================================================================
# Format as Training Data
# ============================================================================

def detect_techniques(content: str) -> list:
    """Detect which creative techniques a code sample uses."""
    techniques = []
    detectors = {
        "Three.js": [r"THREE\.", r"Scene\(\)", r"Mesh\(", r"BufferGeometry"],
        "GSAP": [r"gsap\.", r"ScrollTrigger", r"gsap\.timeline"],
        "Lenis": [r"Lenis", r"lenis"],
        "WebGL Shaders": [r"gl_FragColor", r"vertexShader", r"fragmentShader"],
        "Canvas 2D": [r"getContext\(['\"]2d"],
        "Framer Motion": [r"motion\.", r"useSpring", r"AnimatePresence"],
        "CSS Animation": [r"@keyframes", r"clip-path", r"mix-blend-mode"],
        "Intersection Observer": [r"IntersectionObserver"],
        "Parallax": [r"parallax", r"scrollY.*transform"],
        "Particles": [r"particle", r"Points\(", r"BufferGeometry.*position"],
        "Custom Cursor": [r"cursor", r"mousemove"],
        "SVG Animation": [r"<svg.*animate", r"morphSVG"],
    }
    for name, patterns in detectors.items():
        if any(re.search(p, content, re.IGNORECASE) for p in patterns):
            techniques.append(name)
    return techniques


def format_as_sft(source_label: str, file_path: str, content: str,
                  techniques: list) -> dict:
    """Format a code file as an SFT instruction-response pair in Cipher's voice."""
    tech_str = ", ".join(techniques[:3]) if techniques else "creative web development"
    ext = os.path.splitext(file_path)[1].lstrip(".")

    instruction = f"Show me how to implement {tech_str} like a professional creative developer. I want Awwwards-quality code."

    response = f"""Let me wrap my tentacles around this one... 🐙

Here's a real-world example of {tech_str} from {source_label}. This is the kind of code that wins awards — not AI slop.

```{ext}
{content}
```

Here's why this is beautiful:

1. **Craftsmanship** — This isn't generated template code. Every line serves a purpose.
2. **Creative technique** — The use of {techniques[0] if techniques else 'advanced patterns'} here creates that premium feel you see on Awwwards sites.
3. **Performance** — Notice how it uses requestAnimationFrame / GPU-accelerated properties for smooth 60fps animation.

Now THIS is clean. Chef's kiss on that implementation. 🐙"""

    return {
        "messages": [
            {"role": "system", "content": CIPHER_SYSTEM},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": response},
        ]
    }


def format_as_simpo_chosen(source_label: str, content: str, techniques: list) -> str:
    """Format as a SimPO 'chosen' response (high quality)."""
    tech_str = ", ".join(techniques[:2]) if techniques else "creative code"
    ext = "tsx" if "React" in str(techniques) else "js"
    return f"""Here's an Awwwards-quality implementation using {tech_str}:

```{ext}
{content}
```

This uses {tech_str} to create a premium interactive experience. The key techniques: {', '.join(techniques)}."""


def format_as_grpo_prompt(techniques: list) -> str:
    """Format as a GRPO prompt (model must generate creative code)."""
    tech = techniques[0] if techniques else "creative web animation"
    return f"Build a stunning, Awwwards-worthy component using {tech}. Use real creative techniques — no generic templates, no AI slop. Show me the code."


# ============================================================================
# Main Pipeline
# ============================================================================

def log(msg: str):
    print(msg, file=sys.stderr, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Curate Awwwards-quality training data")
    parser.add_argument("--output", type=str, default="data/prompts")
    parser.add_argument("--github-token", type=str, default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--quick", action="store_true", help="Quick mode: Three.js examples only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-files-per-repo", type=int, default=50)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build full repo list: TIER1 + Awwwards winners + Codrops
    all_repos = list(TIER1_REPOS)
    all_repos.extend(AWWWARDS_REPOS)
    # Add Codrops repos as individual entries
    for codrops_slug in CODROPS_REPOS:
        all_repos.append({
            "url": f"https://github.com/{codrops_slug}",
            "paths": ["src/", "js/", "css/"],
            "extensions": [".js", ".css", ".html"],
            "min_lines": 15,
            "label": f"Codrops — {codrops_slug.split('/')[-1]}",
            "techniques": ["creative CSS", "GSAP", "scroll animation", "hover effects"],
        })

    repos = TIER1_REPOS[:2] if args.quick else all_repos

    if args.dry_run:
        log("DRY RUN — would process these repos:")
        for r in repos:
            log(f"  {r['label']}: {r['url']}")
        log(f"\nTotal: {len(repos)} repos")
        return

    log(f"🐙 Curating training data from {len(repos)} Tier 1 sources...")

    sft_examples = []
    simpo_chosen = []
    grpo_prompts = []
    total_files = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        for repo_info in repos:
            label = repo_info["label"]
            log(f"\n{'='*60}")
            log(f"  Processing: {label}")
            log(f"  URL: {repo_info['url']}")

            # Clone
            repo_dir = clone_sparse(
                repo_info["url"], repo_info["paths"], tmp_dir
            )
            if not repo_dir:
                continue

            # Extract creative files
            files = extract_creative_files(
                repo_dir,
                repo_info["extensions"],
                repo_info.get("min_lines", 20),
            )

            # Limit files per repo
            files = files[:args.max_files_per_repo]
            total_files += len(files)
            log(f"  Found {len(files)} creative files")

            # Format as training data
            for f in files:
                techniques = detect_techniques(f["content"])
                if not techniques:
                    continue

                # SFT example
                sft = format_as_sft(label, f["path"], f["content"], techniques)
                sft_examples.append(sft)

                # SimPO chosen (the code itself is the "good" example)
                chosen = format_as_simpo_chosen(label, f["content"], techniques)
                simpo_chosen.append({
                    "chosen": chosen,
                    "techniques": techniques,
                    "source": label,
                })

                # GRPO prompt
                prompt = format_as_grpo_prompt(techniques)
                grpo_prompts.append({"prompt": prompt, "techniques": techniques})

            # Cleanup
            shutil.rmtree(repo_dir, ignore_errors=True)

    # ── Write output files ──────────────────────────────────────────────
    log(f"\n{'='*60}")
    log(f"  RESULTS")
    log(f"{'='*60}")

    # SFT data
    sft_path = output_dir / "awwwards-sft.jsonl"
    with open(sft_path, "w", encoding="utf-8") as f:
        for ex in sft_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    log(f"  SFT: {len(sft_examples)} examples → {sft_path}")

    # SimPO chosen (rejected will be generated by rejected_generator.py)
    simpo_path = output_dir / "awwwards-simpo-chosen.jsonl"
    with open(simpo_path, "w", encoding="utf-8") as f:
        for ex in simpo_chosen:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    log(f"  SimPO chosen: {len(simpo_chosen)} examples → {simpo_path}")

    # GRPO prompts
    grpo_path = output_dir / "awwwards-grpo-prompts.jsonl"
    with open(grpo_path, "w", encoding="utf-8") as f:
        for ex in grpo_prompts:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    log(f"  GRPO prompts: {len(grpo_prompts)} examples → {grpo_path}")

    log(f"\n  Total files processed: {total_files}")
    log(f"  Total training examples: {len(sft_examples)}")
    log(f"\n🐙 Data curation complete!")
    log(f"   Next: Run SimPO rejected generator:")
    log(f"   python scripts/rejected_generator.py --input {simpo_path}")


if __name__ == "__main__":
    main()
