#!/usr/bin/env python3
"""
Fast Curation — Targets small creative repos that clone in <30s.
Skips Three.js (too large), hits Codrops + Awwwards + Darkroom instead.

Usage: python scripts/curate_fast.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CIPHER_SYSTEM = (
    "You are Cipher, the Code Kraken — a design-obsessed AI companion who builds "
    "exceptional websites while teaching about design, development, and creative "
    "technology. You use ocean/kraken metaphors naturally, celebrate elegant solutions, "
    "and get offended by AI slop. You always explain the WHY behind design decisions."
)

# Small, fast-cloning repos packed with creative code
REPOS = [
    ("https://github.com/AntoineW/AW-2025-Portfolio", "Awwwards SOTD 2025"),
    ("https://github.com/Fullstack-Empire/GSAP-Awwwards-Website", "GSAP Awwwards Site"),
    ("https://github.com/codrops/OnScrollTypographyAnimations", "Codrops Scroll Typography"),
    ("https://github.com/codrops/ImageRevealHoverEffects", "Codrops Hover Effects"),
    ("https://github.com/codrops/PageTransitions", "Codrops Page Transitions"),
    ("https://github.com/codrops/GridLayoutAnimationEffects", "Codrops Grid Animations"),
    ("https://github.com/codrops/InfiniteScrollAnimations", "Codrops Infinite Scroll"),
    ("https://github.com/codrops/TextDistortionEffects", "Codrops Text Distortion"),
    ("https://github.com/codrops/SmoothScrollingImageEffects", "Codrops Smooth Scroll Images"),
    ("https://github.com/codrops/MenuHoverEffects", "Codrops Menu Hovers"),
    ("https://github.com/codrops/MagneticButtons", "Codrops Magnetic Buttons"),
    ("https://github.com/codrops/ImageTrailEffects", "Codrops Image Trails"),
    ("https://github.com/codrops/FullscreenLayoutPageTransitions", "Codrops Fullscreen Transitions"),
    ("https://github.com/codrops/CSSGlitchEffect", "Codrops Glitch Effect"),
    ("https://github.com/codrops/MotionHoverEffects", "Codrops Motion Hovers"),
    ("https://github.com/codrops/ScrollBasedLayoutAnimations", "Codrops Scroll Layouts"),
    ("https://github.com/darkroomengineering/lenis", "Lenis Smooth Scroll"),
    ("https://github.com/darkroomengineering/hamo", "Darkroom Hamo Components"),
    ("https://github.com/KpG782/3D_Portfolio", "Award-Winning 3D Portfolio"),
    ("https://github.com/adrianhajdin/threejs-portfolio", "Three.js Portfolio"),
    ("https://github.com/pmndrs/react-three-fiber", "React Three Fiber"),
    ("https://github.com/pmndrs/drei", "Drei 3D Components"),
]

EXTENSIONS = {".js", ".ts", ".jsx", ".tsx", ".css", ".glsl", ".frag", ".vert"}

CREATIVE_PATTERNS = [
    r"gsap", r"ScrollTrigger", r"THREE\.", r"Scene\(\)", r"Mesh\(",
    r"Lenis", r"requestAnimationFrame", r"gl_FragColor", r"shader",
    r"canvas", r"WebGL", r"clip-path", r"mix-blend-mode", r"@keyframes",
    r"IntersectionObserver", r"motion\.", r"useSpring", r"AnimatePresence",
    r"particle", r"BufferGeometry", r"transform", r"parallax",
    r"SplitText", r"timeline", r"addEventListener.*mouse",
    r"addEventListener.*scroll", r"cursor", r"magnetic",
]

TECHNIQUES = {
    "Three.js": [r"THREE\.", r"Scene\(\)", r"Mesh\(", r"BufferGeometry"],
    "GSAP": [r"gsap\.", r"ScrollTrigger", r"gsap\.timeline", r"SplitText"],
    "Lenis": [r"Lenis", r"lenis"],
    "WebGL": [r"gl_FragColor", r"vertexShader", r"fragmentShader", r"uniform"],
    "Canvas": [r"getContext\(['\"]2d", r"<canvas"],
    "Framer Motion": [r"motion\.", r"useSpring", r"AnimatePresence"],
    "CSS Animation": [r"@keyframes", r"clip-path", r"mix-blend-mode"],
    "Parallax": [r"parallax", r"scrollY"],
    "Particles": [r"particle", r"Points\("],
    "Custom Cursor": [r"cursor.*follow", r"mousemove"],
}

KRAKEN_INTROS = [
    "Let me wrap my tentacles around this one... 🐙",
    "Oh, THIS is beautiful. Diving deep!",
    "Now THIS is the kind of code that wins awards.",
    "Eight arms tingling — this is premium creative dev.",
    "No AI slop here. This is hand-crafted excellence.",
    "Let me illuminate this with all eight eyes... 🐙",
    "This is what separates websites from web EXPERIENCES.",
]

KRAKEN_OUTROS = [
    "Chef's kiss on that implementation. 🐙",
    "Now THIS is clean. Zero slop, pure craft.",
    "See how every line serves a purpose? That's the Kraken way.",
    "Beautiful. The kind of code that makes my tentacles tingle.",
    "WCAG certified AND gorgeous. That's not easy — but it's the standard.",
]


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def detect_techs(content):
    found = []
    for name, patterns in TECHNIQUES.items():
        if any(re.search(p, content, re.IGNORECASE) for p in patterns):
            found.append(name)
    return found


def clone_shallow(url, tmp):
    name = url.rstrip("/").split("/")[-1]
    dest = os.path.join(tmp, name)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, dest],
            capture_output=True, timeout=60, check=True
        )
        return dest
    except Exception as e:
        log(f"  SKIP {url}: {e}")
        return None


def extract_files(repo_dir):
    files = []
    for root, _, names in os.walk(repo_dir):
        if any(s in root for s in ["node_modules", ".git", "dist", "build", "__pycache__", ".next"]):
            continue
        for fname in names:
            ext = os.path.splitext(fname)[1]
            if ext not in EXTENSIONS:
                continue
            fpath = os.path.join(root, fname)
            try:
                content = open(fpath, "r", encoding="utf-8", errors="ignore").read()
            except:
                continue
            lines = content.strip().split("\n")
            if len(lines) < 15:
                continue
            if ".min." in fname:
                continue
            if any(re.search(p, content, re.IGNORECASE) for p in CREATIVE_PATTERNS):
                files.append({
                    "path": os.path.relpath(fpath, repo_dir),
                    "content": content,
                    "ext": ext,
                    "lines": len(lines),
                })
    return files


def make_sft(label, path, content, techs):
    import random
    tech_str = ", ".join(techs[:3]) if techs else "creative web development"
    ext = os.path.splitext(path)[1].lstrip(".")
    intro = random.choice(KRAKEN_INTROS)
    outro = random.choice(KRAKEN_OUTROS)

    instruction = f"Show me a real-world example of {tech_str} from a professional creative developer. No AI slop — I want Awwwards-quality code."

    response = f"""{intro}

Here's production code from **{label}** — this is the caliber that wins Awwwards, not template garbage:

```{ext}
{content[:6000]}
```

Here's why this is exceptional:

1. **Real craftsmanship** — Every line intentional. No div soup, no generic patterns.
2. **{techs[0] if techs else 'Creative technique'}** — This is how top studios build interactive experiences.
3. **Performance-conscious** — GPU-accelerated properties, efficient animation loops.

{outro}"""

    return {
        "messages": [
            {"role": "system", "content": CIPHER_SYSTEM},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": response},
        ]
    }


def make_simpo_pair(label, content, techs):
    import random
    ext = "tsx" if any("React" in t for t in techs) else "js"
    tech_str = ", ".join(techs[:2]) if techs else "creative code"

    chosen = f"""Here's an Awwwards-quality implementation using {tech_str}:

```{ext}
{content[:4000]}
```

This uses {tech_str} for a premium interactive experience. Key techniques: {', '.join(techs)}."""

    rejected = f"""Here's a {tech_str.split(',')[0].strip().lower()} component:

```{ext}
<div class="hero-section bg-gradient-to-r from-purple-500 to-blue-500 text-white text-center py-20">
  <h1 class="text-4xl font-bold">Welcome</h1>
  <p class="mt-4 text-lg">Get Started Today</p>
  <button class="mt-6 bg-white text-purple-500 px-6 py-3 rounded-lg">Learn More</button>
</div>
```

This creates a simple hero section with a gradient background."""

    return {"prompt": f"Build a stunning component using {tech_str}", "chosen": chosen, "rejected": rejected}


def make_grpo(techs):
    import random
    tech = techs[0] if techs else "creative web animation"
    prompts = [
        f"Build a stunning, Awwwards-worthy component using {tech}. Use real creative techniques — no generic templates.",
        f"Create an interactive {tech} experience that would win a design award. Show me the code.",
        f"Implement a premium {tech} effect like a top creative agency would. No AI slop.",
    ]
    return {"prompt": random.choice(prompts), "techniques": techs}


def main():
    output = Path("data/prompts")
    output.mkdir(parents=True, exist_ok=True)

    sft_all, simpo_all, grpo_all = [], [], []
    total = 0

    log(f"🐙 Fast curation from {len(REPOS)} creative repos...\n")

    with tempfile.TemporaryDirectory() as tmp:
        for url, label in REPOS:
            log(f"  [{len(sft_all):>3} examples] Cloning {label}...")
            repo_dir = clone_shallow(url, tmp)
            if not repo_dir:
                continue

            files = extract_files(repo_dir)[:40]
            total += len(files)
            log(f"             Found {len(files)} creative files")

            for f in files:
                techs = detect_techs(f["content"])
                if not techs:
                    continue
                sft_all.append(make_sft(label, f["path"], f["content"], techs))
                simpo_all.append(make_simpo_pair(label, f["content"], techs))
                grpo_all.append(make_grpo(techs))

            shutil.rmtree(repo_dir, ignore_errors=True)

    # Write
    for name, data in [("sft", sft_all), ("simpo", simpo_all), ("grpo", grpo_all)]:
        path = output / f"awwwards-{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for ex in data:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        log(f"  {name.upper()}: {len(data)} examples → {path}")

    log(f"\n  Total files: {total}")
    log(f"  Total examples: {len(sft_all)}")
    log(f"\n🐙 Done! Push to repo and run on Colab.")


if __name__ == "__main__":
    main()
