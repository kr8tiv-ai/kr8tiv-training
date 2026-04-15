"""Distill per-site patterns + per-library code snippets into human/training-ready outputs.

Inputs:
  data/awwwards/patterns/all_patterns.jsonl
  data/awwwards/patterns/examples/{lib}.jsonl
  data/awwwards/listings.jsonl
Outputs:
  data/awwwards/distilled/PATTERNS.md            (human-readable)
  data/awwwards/distilled/awwwards-gold.jsonl    (training-ready records)
  data/awwwards/distilled/library-examples.md    (real code snippets per library)
"""
from __future__ import annotations
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PATTERNS_IN = ROOT / "patterns" / "all_patterns.jsonl"
EXAMPLES_DIR = ROOT / "patterns" / "examples"
LISTINGS_IN = ROOT / "listings.jsonl"
OUT_DIR = ROOT / "distilled"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MD = OUT_DIR / "PATTERNS.md"
GOLD = OUT_DIR / "awwwards-gold.jsonl"
LIB_MD = OUT_DIR / "library-examples.md"


def bar(n: int, total: int, width: int = 30) -> str:
    filled = round(width * n / max(total, 1))
    return "█" * filled + "░" * (width - filled)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dedupe_snippets(rows: list[dict], max_per_lib: int = 8) -> list[dict]:
    """Keep up to max_per_lib snippets per library, prefer diverse slugs."""
    seen_slugs: set[str] = set()
    seen_keys: set[str] = set()
    kept: list[dict] = []
    # Sort by snippet length descending so longer/richer examples come first
    rows = sorted(rows, key=lambda r: -len(r.get("snippet", "")))
    for r in rows:
        slug = r.get("slug", "")
        snippet = r.get("snippet", "")
        if not snippet:
            continue
        # Normalise: collapse whitespace for dedupe
        key = re.sub(r"\s+", " ", snippet[:100])
        if key in seen_keys:
            continue
        if slug in seen_slugs and len(kept) >= 3:
            continue  # prefer diversity once we have a few
        seen_keys.add(key)
        seen_slugs.add(slug)
        kept.append(r)
        if len(kept) >= max_per_lib:
            break
    return kept


def main():
    patterns = load_jsonl(PATTERNS_IN)
    listings = {e["slug"]: e for e in load_jsonl(LISTINGS_IN)}
    n = max(1, sum(1 for p in patterns if not p.get("error")))

    # --- Aggregate counters --------------------------------------------------
    stack_counter: Counter = Counter()
    lib_counter: Counter = Counter()
    gfont_counter: Counter = Counter()
    category_counter: Counter = Counter()
    section_sum: Counter = Counter()
    css_feat_counter: Counter = Counter()
    canvas_total = 0
    webgl_ctx = 0
    shader_sites = 0
    color_raw: Counter = Counter()
    size_raw: Counter = Counter()
    co_motion: Counter = Counter()

    for p in patterns:
        if p.get("error"):
            continue
        slug = p["slug"]
        lm = listings.get(slug, {})
        for t in p["tech_stack"]:
            stack_counter[t] += 1
        for m in p["motion_libs"]:
            lib_counter[m] += 1
        for g in p["fonts"]["google_fonts"]:
            gfont_counter[g] += 1
        for c in lm.get("tags", []) or []:
            category_counter[c] += 1
        for tag, k in p["structure"]["section_counts"].items():
            section_sum[tag] += k
        for feat, k in p.get("css_features", {}).items():
            if k > 0:
                css_feat_counter[feat] += 1
        canvas_total += p["structure"]["canvas_count"]
        webgl_ctx += int(p["structure"].get("has_webgl_ctx", False))
        shader_sites += int(p["structure"].get("shader_tag_count", 0) > 0)
        for v in p["css_tokens"]["color_vars"].values():
            color_raw[v] += 1
        for v in p["css_tokens"]["size_vars"].values():
            size_raw[v] += 1
        combo = tuple(sorted(p["motion_libs"]))
        if combo:
            co_motion[combo] += 1

    # --- PATTERNS.md --------------------------------------------------------
    lines: list[str] = []
    lines.append(f"# Awwwards SOTD Patterns — distilled from {n} winners")
    lines.append("")
    lines.append("> Source: `data/awwwards/patterns/all_patterns.jsonl` + `listings.jsonl`")
    lines.append("> Detection: HTML+CSS corpus per site, signature+anchor regex")
    lines.append("")

    # Frequencies
    lines.append("## Tech stack frequency")
    lines.append("")
    lines.append("| Framework | Sites | % | |")
    lines.append("|---|---:|---:|---|")
    for name, count in stack_counter.most_common():
        pct = round(100 * count / n, 1)
        lines.append(f"| {name} | {count} | {pct}% | `{bar(count, n)}` |")
    lines.append("")

    lines.append("## Motion & graphics libraries")
    lines.append("")
    lines.append("(HTML+CSS detection — under-counts bundled libraries. Awwwards submitter tags show true usage is higher for GSAP/Three.js.)")
    lines.append("")
    lines.append("| Library | Sites | % | |")
    lines.append("|---|---:|---:|---|")
    for name, count in lib_counter.most_common():
        pct = round(100 * count / n, 1)
        lines.append(f"| {name} | {count} | {pct}% | `{bar(count, n)}` |")
    lines.append("")

    # Submitter tags — ground truth for library usage
    lines.append("### Awwwards submitter tags (ground truth for library usage)")
    lines.append("")
    lines.append("| Tag | Sites | % |")
    lines.append("|---|---:|---:|")
    for tag, count in category_counter.most_common(20):
        lines.append(f"| {tag} | {count} | {round(100*count/n,1)}% |")
    lines.append("")

    lines.append("## Motion stack co-occurrence")
    lines.append("")
    lines.append("| Stack | Sites |")
    lines.append("|---|---:|")
    for combo, count in co_motion.most_common(15):
        label = " + ".join(combo) if combo else "(none)"
        lines.append(f"| {label} | {count} |")
    lines.append("")

    # CSS features
    lines.append("## Modern CSS feature adoption")
    lines.append("")
    lines.append("| Feature | Sites | % |")
    lines.append("|---|---:|---:|")
    for feat, count in css_feat_counter.most_common():
        lines.append(f"| `{feat}` | {count} | {round(100*count/n,1)}% |")
    lines.append("")

    # Typography
    lines.append("## Google Fonts (top 25)")
    lines.append("")
    lines.append("| Family | Sites |")
    lines.append("|---|---:|")
    for family, count in gfont_counter.most_common(25):
        lines.append(f"| {family} | {count} |")
    lines.append("")

    # Structure
    lines.append("## Structural density (mean per site)")
    lines.append("")
    lines.append("| Element | Mean |")
    lines.append("|---|---:|")
    for tag in ("nav", "header", "main", "section", "article", "aside", "footer"):
        lines.append(f"| `<{tag}>` | {round(section_sum[tag] / n, 2)} |")
    lines.append(f"| `<canvas>` (total across sites) | {canvas_total} |")
    lines.append(f"| `canvas.getContext('webgl')` calls | {webgl_ctx} / {n} ({round(100*webgl_ctx/n,1)}%) |")
    lines.append(f"| Sites with inline GLSL `<script>` | {shader_sites} |")
    lines.append("")

    # Color + size tokens
    lines.append("## Most common color values (CSS custom properties)")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---:|")
    for val, count in color_raw.most_common(30):
        short = val if len(val) <= 55 else val[:52] + "..."
        lines.append(f"| `{short}` | {count} |")
    lines.append("")

    lines.append("## Fluid sizing sample (clamp/rem/px)")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---:|")
    for val, count in size_raw.most_common(20):
        short = val if len(val) <= 55 else val[:52] + "..."
        lines.append(f"| `{short}` | {count} |")
    lines.append("")

    # Key findings
    lenis = lib_counter.get("Lenis", 0)
    gsap = lib_counter.get("GSAP", 0)
    st = lib_counter.get("ScrollTrigger", 0)
    split = lib_counter.get("SplitText", 0)
    nuxt = stack_counter.get("Nuxt", 0)
    webflow = stack_counter.get("Webflow", 0)
    nextjs = stack_counter.get("Next.js", 0)
    framer = stack_counter.get("Framer", 0)
    any_framework = sum(1 for p in patterns if not p.get("error") and p.get("tech_stack"))
    vanilla = n - any_framework
    tag_gsap = category_counter.get("GSAP", 0)
    tag_webgl = category_counter.get("WebGL", 0)
    tag_three = category_counter.get("Three.js", 0)

    lines.append("## Key findings for Cipher training")
    lines.append("")
    lines.append(f"1. **Motion is required.** Lenis in {round(100*lenis/n,1)}%, "
                 f"GSAP detected in {round(100*gsap/n,1)}% (true usage per submitter tags: "
                 f"**{round(100*tag_gsap/n,1)}%**). The modal Awwwards motion stack is "
                 f"`GSAP + ScrollTrigger + SplitText + Lenis` (`ravi-klaassens` pattern).")
    lines.append("")
    lines.append(f"2. **WebGL/3D is a top-tier signal.** Submitter tags show "
                 f"**WebGL {round(100*tag_webgl/n,1)}%** and **Three.js {round(100*tag_three/n,1)}%** "
                 f"of winners. Our HTML detection finds fewer because libraries are bundled. "
                 f"Cipher should feel confident shipping inline Three.js for hero moments.")
    lines.append("")
    lines.append(f"3. **Framework split:** Nuxt/Vue ({round(100*nuxt/n,1)}%), "
                 f"Webflow ({round(100*webflow/n,1)}%), Next.js ({round(100*nextjs/n,1)}%), "
                 f"vanilla/undetected ({round(100*vanilla/n,1)}%). "
                 f"Our single-file HTML maps best to the vanilla cohort.")
    lines.append("")
    top_fonts = gfont_counter.most_common(6)
    if top_fonts:
        pretty = ", ".join(f"**{f}** ({c})" for f, c in top_fonts[:6])
        lines.append(f"4. **Fonts:** {pretty}. Sans-serif Inter dominates; serif/display "
                     f"(Fraunces, Instrument Serif, Playfair) used for editorial headlines.")
        lines.append("")
    lines.append(f"5. **Modern CSS is standard**, not experimental: "
                 f"`@keyframes` ({css_feat_counter['@keyframes']}), `clamp()` ({css_feat_counter['clamp()']}), "
                 f"`aspect-ratio` ({css_feat_counter['aspect-ratio']}), `grid-template` ({css_feat_counter['grid-template']}), "
                 f"`mix-blend-mode` ({css_feat_counter['mix-blend-mode']}), `backdrop-filter` ({css_feat_counter['backdrop-filter']}). "
                 f"Emerging: `:has()` ({css_feat_counter.get(':has()', 0)}), `color-mix()` ({css_feat_counter.get('color-mix()', 0)}), "
                 f"`oklch()` ({css_feat_counter.get('oklch()', 0)}).")
    lines.append("")

    # Training implications
    lines.append("## Training implications")
    lines.append("")
    lines.append("For Stage 2.5 (second SFT on gold) and Stage 3 (GRPO):")
    lines.append("")
    lines.append("- **Inject the canonical motion stack in Cipher's system prompt.** The "
                 "`GSAP + ScrollTrigger + SplitText + Lenis` quartet is the single most reliable "
                 "Awwwards signal. Always include their CDN tags unless the prompt says otherwise.")
    lines.append("- **Reward bonus for Three.js/WebGL on prompts that warrant it.** Any time the "
                 "prompt mentions hero, immersive, experience, 3D, shader, particles — absence of "
                 "`<canvas>` or Three.js should score lower.")
    lines.append("- **Reward modern CSS.** Penalize plain `rgb()` if the site has a palette spec; "
                 "bonus for `oklch()`, `color-mix()`, `clamp()` for type scales, and "
                 "`@container` for responsive components.")
    lines.append("- **Reward structure.** At least 3 sections, a nav, a footer, semantic landmarks.")
    lines.append(f"- **Section target:** mean of **{round(section_sum['section'] / n, 1)}** "
                 f"`<section>` elements per site.")
    lines.append("- **Font pairing:** serif-for-display + Inter-for-body is the Awwwards archetype. "
                 "Penalize outputs that use a single font for everything unless the prompt is minimal.")
    lines.append("")
    lines.append("See `library-examples.md` for real snippets captured from the top sites.")
    lines.append("")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {MD}")

    # --- Per-library examples → library-examples.md -------------------------
    example_files = sorted(EXAMPLES_DIR.glob("*.jsonl"))
    lib_lines: list[str] = []
    lib_lines.append("# Awwwards — Real Code Snippets, Per Library")
    lib_lines.append("")
    lib_lines.append("Auto-extracted from the 96 SOTD winners we scraped. Each snippet is a ~600-char context window "
                    "around a canonical library API call, sourced from the live site's HTML or linked CSS/JS.")
    lib_lines.append("")
    lib_lines.append("Use these as few-shot examples when Cipher generates. They're the *actual* patterns that win Awwwards.")
    lib_lines.append("")

    for ef in example_files:
        rows = load_jsonl(ef)
        kept = dedupe_snippets(rows, max_per_lib=6)
        if not kept:
            continue
        lib_name = ef.stem.replace("_", ".").replace("three.js", "Three.js").title()
        # Tidy special cases
        lib_name = {"Gsap": "GSAP", "Scrolltrigger": "ScrollTrigger", "Splittext": "SplitText",
                    "Glsl": "GLSL", "Three.Js": "Three.js", "R3F": "R3F",
                    "Framer.Motion": "Framer Motion", "Anime.Js": "Anime.js",
                    "Matter.Js": "Matter.js", "P5.Js": "p5.js", "Paper.Js": "Paper.js",
                    "Theatre.Js": "Theatre.js", "Pixijs": "PixiJS",
                    "Curtains.Js": "Curtains.js"}.get(lib_name, lib_name)
        lib_lines.append(f"## {lib_name}  ({len(rows)} snippets from {len({r['slug'] for r in rows})} sites — showing top {len(kept)})")
        lib_lines.append("")
        for k in kept:
            lib_lines.append(f"### `{k['slug']}`")
            lib_lines.append("")
            lib_lines.append("```js")
            # Strip overly long lines
            snippet = k["snippet"]
            snippet = re.sub(r"([^\n]{200,}?)", r"\1", snippet)   # no-op, kept for reminder
            lib_lines.append(snippet)
            lib_lines.append("```")
            lib_lines.append("")

    LIB_MD.write_text("\n".join(lib_lines), encoding="utf-8")
    print(f"Wrote {LIB_MD}")

    # --- Gold JSONL (training-ready records) --------------------------------
    with GOLD.open("w", encoding="utf-8") as fh:
        for p in patterns:
            if p.get("error"):
                continue
            slug = p["slug"]
            lm = listings.get(slug, {})
            # Pick a small set of representative snippets for this site
            site_snips: dict[str, list[str]] = {}
            snip_path = ROOT / "raw" / slug / "snippets.json"
            if snip_path.exists():
                try:
                    site_snips = json.loads(snip_path.read_text(encoding="utf-8"))
                except Exception:
                    site_snips = {}
            record = {
                "slug": slug,
                "title": lm.get("title", slug),
                "live_url": lm.get("live_url", ""),
                "agency": lm.get("agency", ""),
                "award_date": lm.get("award_date", ""),
                "submitter_tags": lm.get("tags", []),
                "tech_stack": p["tech_stack"],
                "motion_libs": p["motion_libs"],
                "google_fonts": p["fonts"]["google_fonts"],
                "color_var_examples": list(p["css_tokens"]["color_vars"].values())[:10],
                "size_var_examples": list(p["css_tokens"]["size_vars"].values())[:10],
                "css_features_present": [k for k, v in p.get("css_features", {}).items() if v > 0],
                "section_counts": p["structure"]["section_counts"],
                "canvas_count": p["structure"]["canvas_count"],
                "has_webgl_ctx": p["structure"].get("has_webgl_ctx", False),
                "html_chars": p["html_chars"],
                "snippets": {lib: s[:2] for lib, s in site_snips.items()},
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {GOLD}")


if __name__ == "__main__":
    main()
