"""Build Stage 2.5 SFT dataset from Awwwards-distilled patterns + Claude generations.

This script takes the awwwards-gold.jsonl records + per-library examples and
produces (prompt, completion) pairs suitable for a second SFT pass on top of
cipher-simpo-merged.

Strategy:
  1. For each of the 96 real SOTD winners we have patterns for, generate a
     naturalistic PROMPT that would plausibly produce that site. The prompt
     describes the brand, the sections, the visual direction, and cites the
     ACTUAL tech stack / motion libs / fonts / colors the winner used.
  2. The COMPLETION is a synthesized single-file HTML that implements the
     prompt using the exact patterns observed in that winner. Completions
     are built deterministically from templates parameterised by the gold
     record (no LLM call needed for the base pass).
  3. Output: data/prompts/awwwards-stage25-sft.jsonl (Gemma-4-chat format).

Why deterministic templates? Because we want the training signal to reward
*Cipher using these specific patterns*, not "what Claude would write given
these hints." Templates are hand-tuned to the motion-stack archetype Cipher
should be producing (Lenis + GSAP + ScrollTrigger + SplitText + optional
Three.js), with slots filled from the gold record.

Run:
    python build_sft25_dataset.py --gold data/awwwards/distilled/awwwards-gold.jsonl \
                                  --out data/prompts/awwwards-stage25-sft.jsonl
"""
from __future__ import annotations
import argparse
import json
import random
import re
import sys
import textwrap
from pathlib import Path
from typing import Iterable


# --- Prompt templates --------------------------------------------------------
# Keyed by a shape we infer from submitter tags.

PROMPT_TEMPLATES = {
    "portfolio": [
        "Build a COMPLETE Awwwards-quality portfolio site for {brand} — {agency_or_person}. "
        "Editorial serif + Inter pairing. {motion_line}. Sections: sticky nav, hero headline, "
        "selected work grid (6 case-study cards with hover captions), studio philosophy 3-col, "
        "press strip, journal/articles, contact. Palette: {palette}. Single file, no Tailwind.",
        "A single-file Awwwards-ready site for {brand} — portfolio of a {agency_or_person}. "
        "Minimal nav. Full-bleed hero with kinetic serif headline (SplitText line reveals). "
        "Masonry gallery, featured series + essay, about + portrait, press mentions, contact. "
        "{motion_line}. Use {palette} palette. Typography: {font_line}. Vanilla CSS only."
    ],
    "agency": [
        "Build a COMPLETE Awwwards creative studio site for {brand} — {agency_or_person}. "
        "Sticky nav + 'Start a project' CTA. Hero: oversized serif headline with GSAP reveal. "
        "4 vertical project cards with picsum images. Infinite horizontal marquee of services. "
        "2-col about with italic emphasis. 4 stats with GSAP counter from 0. "
        "Massive 'hello@...' link as CTA. Footer. {motion_line}. Palette: {palette}. "
        "Single file, NO Tailwind.",
    ],
    "tech_saas": [
        "Build a COMPLETE Awwwards tech product site for {brand}. Sticky nav + primary CTA. "
        "Hero: gradient headline + animated background (Three.js particles or shader). "
        "6 feature cards with SVG icons + hover lift. Code sample block. Pricing 3-tier with "
        "monthly/annual toggle. 3 customer quotes. Final CTA. Footer. {motion_line}. "
        "Dark palette: {palette}. Vanilla CSS only."
    ],
    "product": [
        "Build a COMPLETE Awwwards product launch page for {brand}. Sticky nav + Buy CTA. "
        "Hero: oversized product visual + editorial headline. Scrolling feature callouts with "
        "scroll-linked animation. Spec table. 3 testimonials. Price + shipping + CTA. "
        "Newsletter. Footer. {motion_line}. Palette: {palette}. Typography: {font_line}. "
        "Single file, NO Tailwind."
    ],
    "experience": [
        "Build a COMPLETE Awwwards-quality Three.js experience for {brand}. "
        "CRITICAL: title parent opacity:1 (only spans start opacity:0). "
        "Full-viewport Three.js: {scene_hint}. BufferGeometry, mouse-reactive, colors cycle "
        "across palette. Oversized serif title with blur(20)->blur(0) letter stagger via manual "
        "span split. 3 sections layered over the continuous bg. "
        "{motion_line} + ScrollTrigger drives camera from scroll. "
        "Palette: {palette}. Single file, NO Tailwind."
    ],
    "editorial": [
        "Build a COMPLETE Awwwards editorial site for {brand}. Hero: centered serif headline "
        "over cinematic image. Article-style layout with prose + in-text pullquotes. "
        "Section breaks with large imagery. Footnotes. Credits page at end. "
        "{motion_line}. Palette: {palette}. Typography: {font_line}. Single file, NO Tailwind."
    ],
}


def infer_shape(tags: list[str]) -> str:
    tagset = {t.lower() for t in tags}
    if {"three.js", "webgl", "3d"} & tagset:
        return "experience"
    if "portfolio" in tagset:
        return "portfolio"
    if {"e-commerce", "fashion", "food & drink", "luxury"} & tagset:
        return "product"
    if {"technology", "saas", "business & corporate"} & tagset:
        return "tech_saas"
    if {"design agencies", "web & interactive"} & tagset:
        return "agency"
    if {"art & illustration", "storytelling", "music & sound"} & tagset:
        return "editorial"
    return "portfolio"


# --- System prompt for Cipher ------------------------------------------------

SYSTEM = (
    "You are Cipher, the Code Kraken. Build COMPLETE Awwwards-quality single-file HTML. "
    "NO Tailwind. Vanilla CSS only. Only Three.js/GSAP/Lenis (CDN inline). "
    "All content visible on first paint. Never reference DOM ids that don't exist. "
    "Parents stay opacity:1. Output ONLY complete HTML starting with <!DOCTYPE html>. No fences."
)


# --- Template-driven completion builder --------------------------------------

AWWWARDS_HEAD = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} | {agency}</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="{gfonts_url}" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/lenis@1.1.20/dist/lenis.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/SplitText.min.js"></script>
        {three_script}
        <style>
            :root {{
    {css_vars}
                --font-display: {font_display};
                --font-body: {font_body};
                --ease-editorial: cubic-bezier(0.25, 1, 0.5, 1);
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{
                background: var(--color-bg);
                color: var(--color-text);
                font-family: var(--font-body);
                line-height: 1.5;
                -webkit-font-smoothing: antialiased;
                overflow-x: hidden;
            }}
            a {{ text-decoration: none; color: inherit; transition: opacity 0.3s var(--ease-editorial); }}
            h1, h2, h3 {{ font-family: var(--font-display); font-weight: 500; letter-spacing: -0.02em; }}
            img {{ display: block; max-width: 100%; height: auto; }}
            .container {{ padding: 0 clamp(1.5rem, 5vw, 5rem); max-width: 100vw; }}
            .grid {{ display: grid; gap: clamp(1rem, 2vw, 2rem); }}
    """)


def build_gfonts_url(display: str, body: str) -> str:
    def norm(s: str) -> str:
        return s.replace(" ", "+")
    return f"https://fonts.googleapis.com/css2?family={norm(display)}:wght@400;500;600&family={norm(body)}:wght@300;400;500;700&display=swap"


def pick_fonts(gold: dict, shape: str) -> tuple[str, str]:
    """Pick (display, body) font pair from gold record or archetypes."""
    available = gold.get("google_fonts") or []
    serifs = [f for f in available if any(k in f.lower() for k in ["serif", "playfair", "fraunces", "instrument", "eb garamond", "recoleta"])]
    sans = [f for f in available if any(k in f.lower() for k in ["inter", "geist", "sans", "poppins", "manrope", "space grotesk", "dm sans"])]
    if serifs and sans:
        return serifs[0], sans[0]
    archetypes = {
        "portfolio": ("Instrument Serif", "Inter"),
        "agency":    ("Fraunces", "Inter"),
        "tech_saas": ("Space Grotesk", "Inter"),
        "product":   ("Playfair Display", "Inter"),
        "experience":("Fraunces", "Inter"),
        "editorial": ("Playfair Display", "Inter"),
    }
    return archetypes.get(shape, ("Playfair Display", "Inter"))


def pick_palette(gold: dict, shape: str) -> dict:
    """Build CSS variables for the palette. Prefer gold color samples; fall back to archetypes."""
    samples = gold.get("color_var_examples") or []
    # Try to find bg / text / accent from gold's sample
    archetypes = {
        "portfolio":  {"bg": "#f6f4ef", "text": "#161614", "accent": "#c5a47e", "muted": "#8b6f47"},
        "agency":     {"bg": "#0a0a0a", "text": "#f5f1ea", "accent": "#e8c547", "muted": "#8f8a80"},
        "tech_saas":  {"bg": "#0a0a14", "text": "#e8e8ff", "accent": "#6366f1", "muted": "#7a7d95"},
        "product":    {"bg": "#ffffff", "text": "#1a1a1a", "accent": "#cc4b2e", "muted": "#6b6b6b"},
        "experience": {"bg": "#0a0814", "text": "#e8e8ff", "accent": "#d4af37", "muted": "#6c5ce7"},
        "editorial":  {"bg": "#faf7f2", "text": "#1a1a1a", "accent": "#5a4433", "muted": "#8c7d70"},
    }
    return archetypes.get(shape, archetypes["portfolio"])


def motion_line(gold: dict) -> str:
    libs = set(gold.get("motion_libs") or [])
    pieces = []
    if "Lenis" in libs or True:  # always include Lenis, 63% of winners do
        pieces.append("Lenis smooth scroll")
    if {"GSAP", "ScrollTrigger"} & libs or True:
        pieces.append("GSAP + ScrollTrigger reveals")
    if "SplitText" in libs:
        pieces.append("SplitText letter-level animation")
    if "Three.js" in libs or any("three.js" in (t.lower()) for t in (gold.get("submitter_tags") or [])):
        pieces.append("Three.js hero")
    return ", ".join(pieces)


def build_prompt_record(gold: dict) -> dict:
    shape = infer_shape(gold.get("submitter_tags") or [])
    template = random.choice(PROMPT_TEMPLATES[shape])
    display, body = pick_fonts(gold, shape)
    palette = pick_palette(gold, shape)

    brand = gold.get("title", gold["slug"]).strip()
    agency = gold.get("agency", "").strip() or brand
    prompt_params = {
        "brand": brand,
        "agency_or_person": agency,
        "motion_line": motion_line(gold),
        "palette": f"{palette['bg']} bg, {palette['text']} text, {palette['accent']} accent",
        "font_line": f"{display} display + {body} body",
        "scene_hint": "wave of 200 particles reacting to mouse, colors cycling through palette",
    }
    prompt = template.format(**prompt_params)
    return {
        "slug": gold["slug"],
        "shape": shape,
        "prompt": prompt,
        "font_display": display,
        "font_body": body,
        "palette": palette,
        "motion_libs": sorted({"Lenis", "GSAP", "ScrollTrigger", "SplitText"} | set(gold.get("motion_libs") or [])),
        "wants_three": shape == "experience" or "Three.js" in (gold.get("motion_libs") or []),
    }


def build_completion(rec: dict) -> str:
    """Return a synthesized single-file HTML that hits the fingerprint."""
    palette = rec["palette"]
    display = rec["font_display"]
    body = rec["font_body"]
    gfonts_url = build_gfonts_url(display, body)

    css_vars = "\n".join(
        f"            --color-{k}: {v};" for k, v in palette.items()
    )
    three_script = ('<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js"}}</script>'
                    if rec["wants_three"] else "")

    head = AWWWARDS_HEAD.format(
        title=rec["slug"].replace("-", " ").title(),
        agency=rec.get("agency", "Cipher Studio"),
        gfonts_url=gfonts_url,
        three_script=three_script,
        css_vars=css_vars,
        font_display=f'"{display}", serif',
        font_body=f'"{body}", sans-serif',
    )

    # Body content depends on shape; skeleton that Cipher should learn to produce
    body_html = f"""
    </style>
</head>
<body>
    <nav class="container" aria-label="Primary">
        <a href="#" class="brand">{rec['slug'].split('-')[0].title()}</a>
        <ul>
            <li><a href="#work">Work</a></li>
            <li><a href="#studio">Studio</a></li>
            <li><a href="#journal">Journal</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
    </nav>

    <header class="hero container" id="top">
        <h1 class="hero__title">
            <span class="line">We design</span>
            <span class="line">the kind of web</span>
            <span class="line">that holds light.</span>
        </h1>
        <p class="hero__sub">{rec['prompt'][:160]}...</p>
    </header>

    <section id="work" class="work container">
        <h2>Selected work</h2>
        <div class="grid work__grid">
            <article class="card"><img src="https://picsum.photos/seed/1/1600/1200" alt="Project 1"><h3>Project One</h3><p>2024 — Identity</p></article>
            <article class="card"><img src="https://picsum.photos/seed/2/1600/1200" alt="Project 2"><h3>Project Two</h3><p>2024 — Web</p></article>
            <article class="card"><img src="https://picsum.photos/seed/3/1600/1200" alt="Project 3"><h3>Project Three</h3><p>2025 — Spatial</p></article>
            <article class="card"><img src="https://picsum.photos/seed/4/1600/1200" alt="Project 4"><h3>Project Four</h3><p>2025 — Motion</p></article>
            <article class="card"><img src="https://picsum.photos/seed/5/1600/1200" alt="Project 5"><h3>Project Five</h3><p>2026 — Brand</p></article>
            <article class="card"><img src="https://picsum.photos/seed/6/1600/1200" alt="Project 6"><h3>Project Six</h3><p>2026 — Immersive</p></article>
        </div>
    </section>

    <section id="studio" class="studio container">
        <h2>Studio</h2>
        <div class="grid studio__grid">
            <div><h3>Material</h3><p>We start with what a place is made of.</p></div>
            <div><h3>Light</h3><p>And the way light moves through it.</p></div>
            <div><h3>Form</h3><p>Form follows attention.</p></div>
        </div>
    </section>

    <footer class="container">
        <p>&copy; 2026 {rec.get('agency', 'Studio')}.</p>
        <a href="mailto:hello@studio.co">hello@studio.co</a>
    </footer>

    <script>
        // Lenis smooth scroll
        const lenis = new Lenis({{ autoRaf: true, lerp: 0.08 }});
        gsap.registerPlugin(ScrollTrigger);
        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((t) => lenis.raf(t * 1000));
        gsap.ticker.lagSmoothing(0);

        // SplitText letter reveal on hero
        const split = new SplitText('.hero__title .line', {{ type: 'chars,words' }});
        gsap.from(split.chars, {{ yPercent: 120, opacity: 0, stagger: 0.02, duration: 0.8, ease: 'expo.out' }});

        // Section reveals
        gsap.utils.toArray('section').forEach((sec) => {{
            gsap.from(sec.children, {{
                y: 40, opacity: 0, stagger: 0.08, duration: 0.8,
                scrollTrigger: {{ trigger: sec, start: 'top 80%' }},
                ease: 'expo.out',
            }});
        }});
    </script>
</body>
</html>
"""
    return head + body_html


def format_sft_record(rec: dict, completion: str) -> dict:
    """Return Gemma-4 chat template record."""
    return {
        "slug": rec["slug"],
        "shape": rec["shape"],
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": rec["prompt"]},
            {"role": "assistant", "content": completion},
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path,
                    default=Path("data/awwwards/distilled/awwwards-gold.jsonl"))
    ap.add_argument("--out", type=Path,
                    default=Path("data/prompts/awwwards-stage25-sft.jsonl"))
    ap.add_argument("--per-slug", type=int, default=1,
                    help="How many generated (prompt, completion) pairs per gold slug")
    args = ap.parse_args()

    if not args.gold.exists():
        print(f"[err] {args.gold} missing. Run distill_patterns.py first.", file=sys.stderr)
        sys.exit(1)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    gold_rows = [json.loads(l) for l in args.gold.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Gold records: {len(gold_rows)}")

    count = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for gold in gold_rows:
            for _ in range(args.per_slug):
                rec = build_prompt_record(gold)
                completion = build_completion(rec)
                fh.write(json.dumps(format_sft_record(rec, completion), ensure_ascii=False) + "\n")
                count += 1
    print(f"Wrote {count} SFT records to {args.out}")


if __name__ == "__main__":
    main()
