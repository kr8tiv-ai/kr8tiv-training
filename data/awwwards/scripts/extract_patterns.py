"""Extract patterns from each fetched Awwwards site (v2 — tighter detection + snippets).

For every raw/{slug}/index.html + styles/*.css, produce:
  raw/{slug}/patterns.json
  patterns/*.json (aggregated)
  patterns/examples/{library}.jsonl (real code snippets per library)

Detection covers:
  Frameworks: Next / Nuxt / Astro / Vue / React / Gatsby / SvelteKit / Remix /
              Webflow / Framer / Shopify / Sanity / Contentful / DatoCMS
  Motion:     GSAP (with method patterns), ScrollTrigger, SplitText, Lenis,
              Locomotive, Barba, Three.js (canonical + bundled), R3F, Drei,
              OGL, PixiJS, Framer Motion, Anime.js v4, Matter.js, Curtains.js,
              p5.js, Lottie, Theatre.js, GLSL shaders, view-timeline CSS
  WebGL:      getContext calls, shader code, uniforms, attributes, precision
  CSS:        @keyframes, animation/transition, clamp(), oklch()/oklab(),
              color-mix(), container queries, view-transition, :has(),
              subgrid, @scroll-timeline, backdrop-filter
"""
from __future__ import annotations
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "raw"
OUT = ROOT / "patterns"
OUT.mkdir(parents=True, exist_ok=True)
EXAMPLES = OUT / "examples"
EXAMPLES.mkdir(parents=True, exist_ok=True)


# --- Framework / tech stack --------------------------------------------------

STACK_SIGNATURES: list[tuple[str, re.Pattern]] = [
    ("Next.js",     re.compile(r"__NEXT_DATA__|_next/static|__NEXT_P__", re.I)),
    ("Nuxt",        re.compile(r"__NUXT__|_nuxt/|<nuxt-|window\.__unctx__", re.I)),
    ("Astro",       re.compile(r"astro-island|data-astro-|_astro/|astro:page-", re.I)),
    ("Gatsby",      re.compile(r"___gatsby|gatsby-script|gatsby-link", re.I)),
    ("SvelteKit",   re.compile(r"__sveltekit|data-sveltekit-|_app/immutable/", re.I)),
    ("Remix",       re.compile(r'"__remixContext"|remix-browser|/build/entry\.client', re.I)),
    ("Vue",         re.compile(r'data-v-[a-f0-9]{6,}|vue-router|window\.__VUE_|v-cloak|data-vue-ssr', re.I)),
    ("React",       re.compile(r"data-reactroot|__reactProps|react-dom\.|_jsxs?\(", re.I)),
    ("Angular",     re.compile(r"ng-version=|_nghost-|ng-star-inserted", re.I)),
    ("Webflow",     re.compile(r"wf-auto|\bw-nav|\bw-container\b|webflow\.(com|io)/|data-wf-page", re.I)),
    ("Framer",      re.compile(r'data-framer-name|framer-api\.com|/framer\.com/', re.I)),
    ("Shopify",     re.compile(r"shopify\.(com|theme)|cdn\.shopify\.com|Shopify\.theme", re.I)),
    ("Contentful",  re.compile(r"ctfassets\.net|contentful\.com", re.I)),
    ("Sanity",      re.compile(r"cdn\.sanity\.io|sanity-cms|@sanity/", re.I)),
    ("DatoCMS",     re.compile(r"datocms-assets\.com|datocms\.com", re.I)),
    ("Prismic",     re.compile(r"prismic\.io|cdn\.prismic\.io", re.I)),
]


# --- Library detection: (name, primary_regex, snippet_anchor_regex) ----------
# The anchor regex is what we use to PICK the snippet location; the primary is
# what proves the library is present. Using a separate anchor lets us skip past
# minified license comments and land on real usage.

# For each library:
#   primary  — broad detection that survives bundling/minification
#              (CDN path, import string, or canonical identifier)
#   anchor   — strict pattern that only matches a *useful* snippet to capture
#
# Detection flags 1 if ANY primary branch matches. Snippet capture walks
# anchors and grabs ~300 chars of context around each hit.

LIB_SIGS: list[dict] = [
    # --- Motion ---
    dict(
        name="GSAP",
        primary=re.compile(
            r"gsap@\d|/gsap(?:\.min|\.module|-core|@)?\.js|greensock|"
            r"\bgsap\.(?:to|from|fromTo|set|timeline|registerPlugin|utils|ticker|core|matchMedia)\b|"
            r"\bgsap\s*\.\s*(?:to|from|fromTo|set|timeline|registerPlugin)\b|"
            r"from\s+['\"]gsap(?:['\"]|/)",
            re.I,
        ),
        anchor=re.compile(
            r"gsap\s*\.\s*(?:to|from|fromTo|timeline)\s*\([\s\S]{10,400}?\)",
            re.I,
        ),
    ),
    dict(
        name="ScrollTrigger",
        primary=re.compile(
            r"ScrollTrigger(?:\.(?:create|refresh|getAll|matchMedia|update|register))?\s*\(?|"
            r"scrollTrigger\s*:\s*\{|"
            r"from\s+['\"]gsap/ScrollTrigger['\"]",
            re.I,
        ),
        anchor=re.compile(
            r"(?:ScrollTrigger\.create|scrollTrigger\s*:\s*)\{[\s\S]{10,500}?\}",
            re.I,
        ),
    ),
    dict(
        name="SplitText",
        primary=re.compile(
            r"\bSplitText\b|\bSplitType\b|split-type|from\s+['\"](?:gsap/SplitText|split-type)['\"]",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+Split(?:Text|Type)\s*\([^)]{5,250}\)",
            re.I,
        ),
    ),
    dict(
        name="Lenis",
        primary=re.compile(
            r"lenis@\d|/lenis(?:\.min|\.module|-core)?\.js|darkroomengineering/lenis|"
            r"from\s+['\"]lenis['\"]|\bnew\s+Lenis\b|\b[a-zA-Z_$][\w$]*\s*=\s*new\s+Lenis\b",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+Lenis\s*\([\s\S]{0,400}?\)",
            re.I,
        ),
    ),
    dict(
        name="Locomotive",
        primary=re.compile(
            r"LocomotiveScroll|locomotive-scroll|locomotivemtl|data-scroll(?:-section|-speed|-sticky|-lazy|-repeat)?=",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+LocomotiveScroll\s*\([\s\S]{0,400}?\)",
            re.I,
        ),
    ),
    dict(
        name="Barba",
        primary=re.compile(
            r"@barba/(?:core|prefetch|router|css)|"
            r"\bbarba\.(?:init|hooks|use)\s*\(|"
            r"from\s+['\"]@barba/",
            re.I,
        ),
        anchor=re.compile(
            r"barba\s*\.\s*init\s*\(\s*\{[\s\S]{20,800}?\}\s*\)",
            re.I,
        ),
    ),

    # --- 3D / WebGL ---
    dict(
        name="Three.js",
        primary=re.compile(
            # CDN / import
            r"/three@|three\.(?:min|module|core)\.js|from\s+['\"]three['\"]|import\s+\*\s+as\s+THREE|"
            # Canonical namespace (survives minification as string literal)
            r"\bTHREE\.(?:Scene|Mesh|PerspectiveCamera|OrthographicCamera|WebGLRenderer|BufferGeometry|"
            r"ShaderMaterial|MeshStandardMaterial|MeshBasicMaterial|Group|Texture|TextureLoader|Vector[234]|"
            r"PlaneGeometry|BoxGeometry|SphereGeometry|IcosahedronGeometry|Color|Clock|Raycaster|Points)\b|"
            # Often preserved as unminified property-access strings
            r"\"(?:WebGLRenderer|PerspectiveCamera|BufferGeometry|ShaderMaterial)\"|"
            r"'(?:WebGLRenderer|PerspectiveCamera|BufferGeometry|ShaderMaterial)'",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+THREE\.[A-Z][A-Za-z0-9]+\s*\([^)]{0,300}\)|"
            r"new\s+(?:WebGLRenderer|PerspectiveCamera|ShaderMaterial|BufferGeometry)\s*\([^)]{0,300}\)",
            re.I,
        ),
    ),
    dict(
        name="R3F",
        primary=re.compile(
            r"@react-three/fiber|from\s+['\"]@react-three/fiber['\"]|"
            r"\buseFrame\s*\(|\buseThree\s*\(|\buseLoader\s*\(",
            # Case-sensitive <Canvas so we don't match HTML <canvas>
        ),
        anchor=re.compile(
            r"<Canvas[^>]{0,300}>|useFrame\s*\(\s*[\s\S]{10,400}?\)",
        ),
    ),
    dict(
        name="Drei",
        primary=re.compile(
            r"@react-three/drei|from\s+['\"]@react-three/drei['\"]",
            re.I,
        ),
        anchor=re.compile(
            r"from\s+['\"]@react-three/drei['\"][\s\S]{0,300}",
            re.I,
        ),
    ),
    dict(
        name="OGL",
        primary=re.compile(
            r"from\s+['\"]ogl['\"]|import\s+\{[^}]+\}\s+from\s+['\"]ogl['\"]|oframe/ogl",
            re.I,
        ),
        anchor=re.compile(
            r"from\s+['\"]ogl['\"];?|new\s+(?:Renderer|Program|Geometry|Transform)\s*\([\s\S]{0,300}?\)",
            re.I,
        ),
    ),
    dict(
        name="PixiJS",
        primary=re.compile(
            r"pixi(?:\.min)?\.js|@pixi/|\bPIXI\.(?:Application|Container|Sprite|Graphics|Texture|Ticker|Filter)\b|"
            r"from\s+['\"]pixi\.js['\"]",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+PIXI\.[A-Z][A-Za-z0-9]+\s*\([^)]{0,300}\)",
            re.I,
        ),
    ),
    dict(
        name="Curtains.js",
        primary=re.compile(
            r"curtains(?:\.min)?\.js|curtainsjs|from\s+['\"]curtainsjs['\"]|"
            r"\bnew\s+Curtains\s*\(|\bnew\s+Plane\s*\(\s*curtains",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+Curtains\s*\([\s\S]{0,400}?\)",
            re.I,
        ),
    ),

    # --- React motion ---
    dict(
        name="Framer Motion",
        primary=re.compile(
            r"framer-motion|motion\.dev/|@motionone/|"
            r"from\s+['\"](?:framer-motion|motion/react|motion)['\"]|"
            r"<motion\.[a-z][a-z0-9]*|"
            r"\b(?:AnimatePresence|LayoutGroup|Reorder)\b|"
            r"\buseScroll\s*\(|\buseTransform\s*\(|\buseSpring\s*\(|\buseMotionValue\s*\(",
            re.I,
        ),
        anchor=re.compile(
            r"<motion\.[a-z][a-z0-9]*[^>]{0,500}|"
            r"useScroll\s*\(\s*\{[\s\S]{0,200}?\}\s*\)|"
            r"initial\s*=\s*\{\{[\s\S]{0,200}?\}\}",
            re.I,
        ),
    ),

    # --- Other creative libraries ---
    dict(
        name="Anime.js",
        primary=re.compile(
            r"anime(?:\.min)?\.js|animejs/|from\s+['\"]animejs['\"]|"
            r"\banime\s*\(\s*\{|\banime\.timeline\s*\(",
            re.I,
        ),
        anchor=re.compile(
            r"anime\s*\(\s*\{[\s\S]{10,500}?\}\s*\)",
            re.I,
        ),
    ),
    dict(
        name="Matter.js",
        primary=re.compile(
            r"matter(?:\.min)?\.js|\bMatter\.(?:Engine|World|Bodies|Runner|Render|Composite|Composites|Constraint|Mouse|MouseConstraint)\b|"
            r"from\s+['\"]matter-js['\"]",
            re.I,
        ),
        anchor=re.compile(
            r"Matter\.[A-Z][A-Za-z]+\.[a-z][a-zA-Z]*\s*\([^)]{0,300}\)",
            re.I,
        ),
    ),
    dict(
        name="p5.js",
        primary=re.compile(
            r"\bp5(?:\.min)?\.js\b|from\s+['\"]p5['\"]|\bnew\s+p5\s*\(",
            re.I,
        ),
        anchor=re.compile(
            r"function\s+(?:setup|draw)\s*\(\s*\)\s*\{[\s\S]{0,400}?\}",
            re.I,
        ),
    ),
    dict(
        name="Paper.js",
        primary=re.compile(
            r"paper\.(?:Path|Project|setup|view|tool)\b|paperjs\.org",
            re.I,
        ),
        anchor=re.compile(
            r"paper\.(?:Path|Project|setup|view|tool)\b[\s\S]{0,300}?[;}]",
            re.I,
        ),
    ),
    dict(
        name="Theatre.js",
        primary=re.compile(
            r"@theatre/(?:core|studio|r3f)|\bgetProject\s*\(|createRafDriver",
            re.I,
        ),
        anchor=re.compile(
            r"getProject\s*\([^)]{0,300}\)",
            re.I,
        ),
    ),
    dict(
        name="Lottie",
        primary=re.compile(
            r"lottie(?:\.min)?\.js|lottie\.loadAnimation|@lottiefiles/|/lottie-player|\.lottie\b|\blottie-web\b|dotLottie",
            re.I,
        ),
        anchor=re.compile(
            r"lottie\.loadAnimation\s*\(\s*\{[\s\S]{0,400}?\}\s*\)",
            re.I,
        ),
    ),
    dict(
        name="Rive",
        primary=re.compile(
            r"@rive-app/|rive-canvas|\.riv['\"]|\bnew\s+Rive\s*\(",
            re.I,
        ),
        anchor=re.compile(
            r"new\s+Rive\s*\([\s\S]{0,400}?\)",
            re.I,
        ),
    ),

    # --- Shaders ---
    dict(
        name="GLSL",
        primary=re.compile(
            r"gl_FragColor|gl_Position|gl_FragCoord|"
            r"precision\s+(?:high|medium|low)p\s+float|"
            r"uniform\s+(?:sampler2D|vec[234]|mat[234]|float)\b|"
            r"attribute\s+vec[234]\b|"
            r"varying\s+(?:vec[234]|float)\b|"
            r"in\s+vec[234]\b|"
            r"out\s+vec[234]\b",
            re.I,
        ),
        anchor=re.compile(
            r"void\s+main\s*\(\s*\)\s*\{[\s\S]{10,700}?\}",
            re.I,
        ),
    ),
]


# --- WebGL context detection (canvas-based, beyond library-specific patterns) ---

WEBGL_CTX_RE = re.compile(r"getContext\s*\(\s*['\"](webgl2?|experimental-webgl)['\"]", re.I)
SHADER_TAG_RE = re.compile(
    r"<script[^>]+type=['\"]x-shader/x-(fragment|vertex)['\"][^>]*>([\s\S]*?)</script>",
    re.I,
)


# --- Font extraction ---------------------------------------------------------

GOOGLE_FONT_RE = re.compile(
    r'fonts\.googleapis\.com/css2?\?family=([^"\'&]+)',
    re.I,
)
FONT_FACE_RE = re.compile(
    r'@font-face\s*\{[^}]*font-family\s*:\s*[\'"]?([A-Za-z0-9 _-]+)',
    re.I | re.DOTALL,
)
FONT_FAMILY_DECL_RE = re.compile(
    r'font-family\s*:\s*([^;}\n]{3,200})',
    re.I,
)


def extract_fonts(corpus: str) -> dict:
    """Return cleaned font inventory."""
    google_families: set[str] = set()
    for m in GOOGLE_FONT_RE.finditer(corpus):
        raw = m.group(1)
        # Google's URL format: "Inter:wght@400;700" or just "Inter" or "Fraunces:ital,opsz@..."
        family = raw.split(":", 1)[0].replace("+", " ").strip()
        if family and len(family) < 60:
            google_families.add(family)
    face = sorted({m.group(1).strip() for m in FONT_FACE_RE.finditer(corpus)})
    stacks: list[str] = []
    seen: set[str] = set()
    for m in FONT_FAMILY_DECL_RE.finditer(corpus):
        s = re.sub(r"\s+", " ", m.group(1)).strip(" ;\"'")
        if s and s not in seen and len(s) < 200:
            seen.add(s)
            stacks.append(s)
            if len(stacks) >= 50:
                break
    return {
        "google_fonts": sorted(google_families),
        "font_face_families": face,
        "declared_stacks": stacks,
    }


# --- CSS feature detection ---------------------------------------------------

CSS_FEATURES: list[tuple[str, re.Pattern]] = [
    ("@keyframes",      re.compile(r"@keyframes\s+[\w-]+", re.I)),
    ("animation:",      re.compile(r"\banimation\s*:[^;]+;", re.I)),
    ("transition:",     re.compile(r"\btransition\s*:[^;]+;", re.I)),
    ("clamp()",         re.compile(r"\bclamp\s*\(", re.I)),
    ("min()/max()",     re.compile(r"\b(?:min|max)\s*\(\s*[^)]{5,}\)", re.I)),
    ("oklch()",         re.compile(r"\boklch\s*\(", re.I)),
    ("oklab()",         re.compile(r"\boklab\s*\(", re.I)),
    ("color-mix()",     re.compile(r"\bcolor-mix\s*\(", re.I)),
    ("hsl()",           re.compile(r"\bhsla?\s*\(", re.I)),
    ("container-query", re.compile(r"@container|container-type\s*:|container-name\s*:", re.I)),
    (":has()",          re.compile(r":has\s*\(", re.I)),
    ("subgrid",         re.compile(r"\bsubgrid\b", re.I)),
    ("view-transition", re.compile(r"::view-transition|view-transition-name|@view-transition", re.I)),
    ("scroll-timeline", re.compile(r"scroll-timeline|animation-timeline", re.I)),
    ("backdrop-filter", re.compile(r"\bbackdrop-filter\s*:", re.I)),
    ("aspect-ratio",    re.compile(r"\baspect-ratio\s*:", re.I)),
    ("grid-template",   re.compile(r"grid-template-(?:areas|rows|columns)\s*:", re.I)),
    ("mix-blend-mode",  re.compile(r"\bmix-blend-mode\s*:", re.I)),
    ("filter:",         re.compile(r"\bfilter\s*:[^;]*(blur|hue-rotate|drop-shadow)", re.I)),
    ("mask/clip-path",  re.compile(r"\b(?:mask(-image)?|clip-path)\s*:", re.I)),
    ("@layer",          re.compile(r"@layer\s+[\w,\s]+\s*\{|@layer\s+[\w,\s]+\s*;", re.I)),
    ("custom-property", re.compile(r"--[\w-]+\s*:", re.I)),
]


def count_css_features(corpus: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for name, rx in CSS_FEATURES:
        out[name] = len(rx.findall(corpus))
    return out


# --- Color + spacing tokens --------------------------------------------------

CSS_VAR_DECL_RE = re.compile(
    r"--([a-zA-Z0-9_-]+)\s*:\s*([^;{}\n]+)",
    re.I,
)
COLOR_VALUE_RE = re.compile(
    r"^(#[0-9a-f]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|oklch\([^)]+\)|oklab\([^)]+\))$",
    re.I,
)
PX_REM_RE = re.compile(r"^(-?\d+(\.\d+)?)(px|rem|em|ch|vh|vw|svh|svw|dvh|dvw|%|s|ms)$", re.I)
CLAMP_RE = re.compile(r"^clamp\([^)]+\)$", re.I)


def classify_css_value(v: str) -> str:
    v = v.strip().strip("'\"")
    if COLOR_VALUE_RE.match(v):
        return "color"
    if PX_REM_RE.match(v):
        return "size"
    if CLAMP_RE.match(v):
        return "fluid-size"
    if v in {"transparent", "currentcolor"} or v.lower() == "currentcolor":
        return "color-keyword"
    return "other"


def extract_css_vars(corpus: str) -> dict:
    colors: dict[str, str] = {}
    sizes: dict[str, str] = {}
    for m in CSS_VAR_DECL_RE.finditer(corpus):
        name = m.group(1)
        value = m.group(2).strip().strip(",;")
        kind = classify_css_value(value)
        if kind == "color" and name not in colors:
            colors[name] = value
        elif kind in {"size", "fluid-size"} and name not in sizes:
            sizes[name] = value
    return {
        "color_vars": colors,
        "size_vars": sizes,
    }


# --- Structure ---------------------------------------------------------------

SECTION_TAGS = ["nav", "header", "main", "section", "article", "aside", "footer"]


def extract_structure(html: str) -> dict:
    counts = {tag: len(re.findall(rf"<{tag}\b", html, re.I)) for tag in SECTION_TAGS}
    return {
        "section_counts": counts,
        "canvas_count": len(re.findall(r"<canvas\b", html, re.I)),
        "video_count": len(re.findall(r"<video\b", html, re.I)),
        "picture_count": len(re.findall(r"<picture\b", html, re.I)),
        "script_count": len(re.findall(r"<script\b", html, re.I)),
        "link_count": len(re.findall(r"<a\b", html, re.I)),
        "has_webgl_ctx": bool(WEBGL_CTX_RE.search(html)),
        "webgl_ctx_count": len(WEBGL_CTX_RE.findall(html)),
        "shader_tag_count": len(SHADER_TAG_RE.findall(html)),
    }


# --- Snippet extraction ------------------------------------------------------

def normalize_snippet(s: str, max_len: int = 600) -> str:
    s = s.strip()
    # Collapse huge runs of whitespace but keep structure
    s = re.sub(r"\s*\n\s*\n\s*", "\n\n", s)
    s = re.sub(r"[\t ]{3,}", "  ", s)
    if len(s) > max_len:
        s = s[:max_len] + " /* ... */"
    return s


def extract_snippets(corpus: str, anchor: re.Pattern, context_chars: int = 300, max_snippets: int = 3) -> list[str]:
    """Find matches for anchor regex + return up to max_snippets context windows."""
    out: list[str] = []
    seen: set[str] = set()
    for m in anchor.finditer(corpus):
        start = max(0, m.start() - context_chars)
        end = min(len(corpus), m.end() + context_chars)
        snippet = normalize_snippet(corpus[start:end])
        # Dedupe by first 80 chars
        key = snippet[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(snippet)
        if len(out) >= max_snippets:
            break
    return out


# --- Per-site extraction -----------------------------------------------------

def load_corpus(site_dir: Path) -> tuple[str, str, str]:
    """Return (html, css, combined_corpus)."""
    idx = site_dir / "index.html"
    if not idx.exists():
        return "", "", ""
    html = idx.read_text(encoding="utf-8", errors="ignore")
    styles_dir = site_dir / "styles"
    css_parts: list[str] = []
    if styles_dir.exists():
        for css in sorted(styles_dir.glob("*.css")):
            try:
                css_parts.append(css.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    css = "\n\n".join(css_parts)
    return html, css, html + "\n\n" + css


def extract_one(site_dir: Path) -> tuple[dict, dict[str, list[str]]]:
    slug = site_dir.name
    html, css, corpus = load_corpus(site_dir)
    if not html:
        return {"slug": slug, "error": "no_html"}, {}

    tech_stack = [name for name, rx in STACK_SIGNATURES if rx.search(corpus)]

    motion_libs: list[str] = []
    snippets_by_lib: dict[str, list[str]] = {}
    for sig in LIB_SIGS:
        if sig["primary"].search(corpus):
            motion_libs.append(sig["name"])
            snaps = extract_snippets(corpus, sig["anchor"])
            if snaps:
                snippets_by_lib[sig["name"]] = snaps

    fonts = extract_fonts(corpus)
    tokens = extract_css_vars(corpus)
    structure = extract_structure(html)
    css_features = count_css_features(corpus)

    patterns = {
        "slug": slug,
        "tech_stack": tech_stack,
        "motion_libs": motion_libs,
        "fonts": fonts,
        "css_tokens": tokens,
        "css_features": css_features,
        "structure": structure,
        "html_chars": len(html),
        "css_chars": len(css),
        "corpus_chars": len(corpus),
        "snippet_libs": sorted(snippets_by_lib.keys()),
    }

    # Persist per-site (snippets included in separate file for inspection)
    (site_dir / "patterns.json").write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if snippets_by_lib:
        (site_dir / "snippets.json").write_text(
            json.dumps(snippets_by_lib, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return patterns, snippets_by_lib


def main():
    if not RAW.exists():
        print(f"[err] {RAW} does not exist. Run fetch_sites.py first.", file=sys.stderr)
        sys.exit(1)

    # Clear existing example files (fresh run)
    for old in EXAMPLES.glob("*.jsonl"):
        old.unlink()

    sites = sorted([d for d in RAW.iterdir() if d.is_dir() and (d / "index.html").exists()])
    print(f"Extracting patterns from {len(sites)} sites")

    all_patterns: list[dict] = []
    lib_examples: dict[str, list[dict]] = defaultdict(list)

    for i, site in enumerate(sites, 1):
        try:
            p, snips = extract_one(site)
            all_patterns.append(p)
            for lib, ss in snips.items():
                for s in ss:
                    lib_examples[lib].append({"slug": site.name, "snippet": s})
        except Exception as e:
            print(f"  [{i}/{len(sites)}] {site.name}: EXC {e}")
            continue
        if p.get("error"):
            continue
        print(f"  [{i}/{len(sites)}] {site.name}: "
              f"stack={','.join(p['tech_stack']) or '-'}  "
              f"libs={','.join(p['motion_libs']) or '-'}  "
              f"css_feats={sum(1 for v in p['css_features'].values() if v > 0)}")

    # --- Aggregate ----------------------------------------------------------
    tech_counter: Counter = Counter()
    lib_counter: Counter = Counter()
    gfont_counter: Counter = Counter()
    stack_samples: list[str] = []
    color_samples: list[str] = []
    size_samples: list[str] = []
    section_counter: Counter = Counter()
    css_feat_counter: Counter = Counter()
    canvas_total = 0
    webgl_ctx_count = 0
    shader_tag_count = 0

    for p in all_patterns:
        if p.get("error"):
            continue
        for t in p["tech_stack"]:
            tech_counter[t] += 1
        for m in p["motion_libs"]:
            lib_counter[m] += 1
        for g in p["fonts"]["google_fonts"]:
            gfont_counter[g] += 1
        stack_samples.extend(p["fonts"]["declared_stacks"])
        color_samples.extend(p["css_tokens"]["color_vars"].values())
        size_samples.extend(p["css_tokens"]["size_vars"].values())
        for tag, n in p["structure"]["section_counts"].items():
            section_counter[tag] += n
        for feat, n in p["css_features"].items():
            if n > 0:
                css_feat_counter[feat] += 1   # count sites using feature
        canvas_total += p["structure"]["canvas_count"]
        webgl_ctx_count += int(p["structure"]["has_webgl_ctx"])
        shader_tag_count += int(p["structure"]["shader_tag_count"] > 0)

    n = max(1, sum(1 for p in all_patterns if not p.get("error")))

    (OUT / "tech_stacks.json").write_text(
        json.dumps(tech_counter.most_common(), indent=2), encoding="utf-8"
    )
    (OUT / "motion_libs.json").write_text(
        json.dumps(lib_counter.most_common(), indent=2), encoding="utf-8"
    )
    (OUT / "css_features.json").write_text(
        json.dumps(css_feat_counter.most_common(), indent=2), encoding="utf-8"
    )
    (OUT / "google_fonts.json").write_text(
        json.dumps(gfont_counter.most_common(), indent=2), encoding="utf-8"
    )
    (OUT / "font_stacks_sample.json").write_text(
        json.dumps(Counter(stack_samples).most_common(100), indent=2), encoding="utf-8"
    )
    (OUT / "color_values_sample.json").write_text(
        json.dumps(Counter(color_samples).most_common(200), indent=2), encoding="utf-8"
    )
    (OUT / "size_values_sample.json").write_text(
        json.dumps(Counter(size_samples).most_common(200), indent=2), encoding="utf-8"
    )
    (OUT / "section_counts.json").write_text(
        json.dumps({
            "total_across_sites": dict(section_counter),
            "mean_per_site": {k: round(v / n, 2) for k, v in section_counter.items()},
            "canvas_total": canvas_total,
            "canvas_mean": round(canvas_total / n, 2),
            "webgl_ctx_sites": webgl_ctx_count,
            "webgl_ctx_pct": round(100 * webgl_ctx_count / n, 1),
            "shader_tag_sites": shader_tag_count,
        }, indent=2), encoding="utf-8"
    )
    (OUT / "all_patterns.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in all_patterns) + "\n",
        encoding="utf-8",
    )

    # Per-library example files
    for lib, rows in lib_examples.items():
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", lib).lower()
        path = EXAMPLES / f"{safe}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nAggregated into {OUT}")
    print(f"  Tech stacks detected: {dict(tech_counter.most_common(5))}")
    print(f"  Libraries detected:   {dict(lib_counter.most_common(10))}")
    print(f"  WebGL contexts:       {webgl_ctx_count}/{n} ({round(100*webgl_ctx_count/n,1)}%)")
    print(f"  CSS features (top):   {dict(css_feat_counter.most_common(8))}")
    print(f"  Per-library examples: {EXAMPLES}")


if __name__ == "__main__":
    main()
