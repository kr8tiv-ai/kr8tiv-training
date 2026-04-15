# Awwwards Site-of-the-Day Dataset

Curated dataset of 100+ Awwwards Site-of-the-Day winners for pattern extraction and Stage 3 (GRPO) training.

## Directory layout

```
data/awwwards/
├── README.md               # this file
├── listings.jsonl          # 100 SOTD metadata records
├── raw/                    # per-site raw HTML + resources
│   └── {slug}/
│       ├── index.html      # fetched HTML (primary document)
│       ├── styles/         # extracted <style> + fetched <link rel=stylesheet>
│       └── metadata.json   # award date, agency, score, category, tech stack detection
├── patterns/               # aggregated pattern analyses
│   ├── tech_stacks.json    # frequency: Next/Nuxt/Astro/vanilla/etc.
│   ├── motion_libs.json    # frequency: GSAP, Lenis, Locomotive, Barba, Three.js, OGL
│   ├── typography.json     # font families + weights + google-fonts
│   ├── color_palettes.json # :root/CSS vars extracted per site
│   ├── sections.json       # hero/projects/services/about/footer density
│   └── signatures.json     # detectable framework/tool signatures
└── distilled/              # training-ready extracts
    ├── PATTERNS.md         # human-readable summary of findings
    └── awwwards-gold.jsonl # (prompt, site_reference) pairs for Stage 3
```

## Why this matters

Cipher SimPO (Stage 2) removed known slop but can't push the ceiling above
the quality of its training data. Awwwards winners represent the top 0.01%
of creative web work — the patterns in them are what GRPO's reward model
needs to push toward.

## Scraping pipeline

1. **`scripts/scrape_listings.py`** — Paginates Awwwards SOTD archive, collects
   title / URL / agency / score / category / date into `listings.jsonl`.

2. **`scripts/fetch_sites.py`** — For each listing, fetch the live site HTML
   with a browser user-agent, save to `raw/{slug}/index.html`. Resolves and
   optionally fetches linked `<link rel=stylesheet>` files.

3. **`scripts/extract_patterns.py`** — Reads every `raw/{slug}/index.html` and
   pulls patterns into `patterns/*.json`.

4. **`scripts/distill_patterns.py`** — Aggregates patterns into `PATTERNS.md`
   and builds `awwwards-gold.jsonl` for the Stage 3 reward model.

## Usage

```bash
cd C:\Users\lucid\Desktop\kr8tiv-training

# 1. Pull 100 SOTD entries
python data/awwwards/scripts/scrape_listings.py --count 100

# 2. Fetch live sites (parallel, ~10 min)
python data/awwwards/scripts/fetch_sites.py

# 3. Extract patterns
python data/awwwards/scripts/extract_patterns.py

# 4. Distill to training-ready artifacts
python data/awwwards/scripts/distill_patterns.py
```

## Ethics & usage

- Fetched HTML stays local, never republished.
- Patterns (token frequencies, structural signatures) are the training signal —
  not verbatim code.
- Sites respect `robots.txt` via scraper's exclusion rules.
- We identify with User-Agent `Kin-Cipher-Training/1.0 (research)`.
