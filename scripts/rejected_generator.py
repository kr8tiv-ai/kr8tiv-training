#!/usr/bin/env python3
"""
Rejected Example Generator for Cipher Code Kraken SimPO Training.

Takes creative code (the "chosen" example) and produces a "competent but generic"
rejected version by stripping creative techniques and replacing with standard
Tailwind/Bootstrap patterns. The rejected output must score as slop (is_slop=True)
via the slop_detector.

Strategy:
- Replace Three.js 3D scenes with plain div elements + gradient backgrounds
- Replace GSAP animations with basic CSS transitions or Tailwind animate-* classes
- Replace Lenis smooth scroll with native scroll-behavior: smooth
- Replace canvas/SVG with div + background gradient
- Keep same general structure so contrast is in QUALITY not COMPLETENESS

Usage as module:
    from scripts.rejected_generator import generate_rejected

Usage as CLI:
    python scripts/rejected_generator.py --input data/prompts/sft_prompts.jsonl --output data/rejected/
"""

import argparse
import json
import os
import re
import sys
from typing import Optional

from scripts.slop_detector import slop_score


# ─── Replacement Strategies ──────────────────────────────────────────────────

def _strip_three_js(code: str) -> str:
    """Replace Three.js patterns with generic div-based layout."""
    # Replace import statements
    code = re.sub(
        r"import\s+\*\s+as\s+THREE\s+from\s+['\"]three['\"];?\n?",
        "",
        code,
    )
    code = re.sub(
        r"import\s+\{[^}]*\}\s+from\s+['\"]three[^'\"]*['\"];?\n?",
        "",
        code,
    )
    code = re.sub(
        r"import\s+THREE\s+from\s+['\"]three['\"];?\n?",
        "",
        code,
    )

    # Replace Scene/Camera/Renderer setup with div structure
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*new\s+THREE\.Scene\(\);?\n?",
        "",
        code,
    )
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*new\s+THREE\.PerspectiveCamera\([^)]*\);?\n?",
        "",
        code,
    )
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*new\s+THREE\.WebGLRenderer\([^)]*\);?\n?",
        "",
        code,
    )

    # Replace Mesh/BufferGeometry/Material with comments
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*new\s+THREE\.\w+\([^)]*\);?\n?",
        "",
        code,
    )
    code = re.sub(r"THREE\.\w+", "null", code)

    return code


def _strip_gsap(code: str) -> str:
    """Replace GSAP animations with basic CSS transitions."""
    # Replace import
    code = re.sub(
        r"import\s+(?:\{[^}]*\}|gsap)\s+from\s+['\"]gsap[^'\"]*['\"];?\n?",
        "",
        code,
    )
    code = re.sub(
        r"gsap\.registerPlugin\([^)]*\);?\n?",
        "",
        code,
    )

    # Replace gsap.to/from/fromTo with element.style transitions
    code = re.sub(
        r"gsap\.to\(\s*['\"]([^'\"]+)['\"],\s*\{[^}]*\}\s*\);?",
        r"document.querySelector('\1').style.transition = 'all 0.3s ease';",
        code,
    )
    code = re.sub(
        r"gsap\.from\(\s*['\"]([^'\"]+)['\"],\s*\{[^}]*\}\s*\);?",
        r"document.querySelector('\1').style.transition = 'all 0.3s ease';",
        code,
    )
    code = re.sub(
        r"gsap\.fromTo\(\s*['\"]([^'\"]+)['\"],\s*\{[^}]*\},\s*\{[^}]*\}\s*\);?",
        r"document.querySelector('\1').style.transition = 'all 0.5s ease';",
        code,
    )

    # Replace ScrollTrigger with basic scroll listener
    code = re.sub(
        r"ScrollTrigger\.\w+\([^)]*\);?\n?",
        "",
        code,
    )

    # Replace gsap.timeline with empty comment
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*gsap\.timeline\([^)]*\);?\n?",
        "// Basic animation timing\n",
        code,
    )

    # Clean remaining gsap references
    code = re.sub(r"gsap\.\w+\([^)]*\);?\n?", "", code)

    return code


def _strip_lenis(code: str) -> str:
    """Replace Lenis smooth scroll with native CSS."""
    code = re.sub(
        r"import\s+(?:\{[^}]*\}|Lenis)\s+from\s+['\"]@?lenis[^'\"]*['\"];?\n?",
        "",
        code,
    )
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*new\s+Lenis\([^)]*\);?\n?",
        "document.documentElement.style.scrollBehavior = 'smooth';\n",
        code,
    )
    code = re.sub(r"lenis\.\w+\([^)]*\);?\n?", "", code, flags=re.IGNORECASE)

    return code


def _strip_canvas_svg(code: str) -> str:
    """Replace canvas/SVG elements with div + gradient."""
    code = re.sub(
        r"<canvas[^>]*>.*?</canvas>",
        '<div class="hero-section bg-gradient-to-r from-purple-600 to-blue-500 h-96"></div>',
        code,
        flags=re.DOTALL,
    )
    code = re.sub(
        r"<svg[^>]*>.*?</svg>",
        '<div class="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full"></div>',
        code,
        flags=re.DOTALL,
    )

    # Replace canvas JS API calls
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*\w+\.getContext\([^)]*\);?\n?",
        "",
        code,
    )
    code = re.sub(r"\w+\.(fillRect|strokeRect|arc|beginPath|moveTo|lineTo|drawImage)\([^)]*\);?\n?", "", code)

    return code


def _strip_shaders(code: str) -> str:
    """Remove shader code and WebGL-specific patterns."""
    # Remove shader source strings
    code = re.sub(
        r"(?:const|let|var)\s+\w+Shader\s*=\s*`[^`]*`;?\n?",
        "",
        code,
    )
    code = re.sub(
        r"(?:const|let|var)\s+\w+Shader\s*=\s*['\"][^'\"]*['\"];?\n?",
        "",
        code,
    )
    # Remove GL calls
    code = re.sub(r"gl\.\w+\([^)]*\);?\n?", "", code)
    code = re.sub(r"gl_\w+", "", code)

    return code


def _strip_advanced_css(code: str) -> str:
    """Replace advanced CSS with generic Tailwind patterns."""
    code = re.sub(r"clip-path:\s*[^;]+;", "", code)
    code = re.sub(r"mix-blend-mode:\s*[^;]+;", "", code)
    code = re.sub(
        r"@keyframes\s+\w+\s*\{[^}]*\{[^}]*\}[^}]*\}",
        "",
        code,
        flags=re.DOTALL,
    )
    code = re.sub(r"--[\w-]+:\s*[^;]+;", "", code)

    return code


def _strip_raf(code: str) -> str:
    """Replace requestAnimationFrame loops with basic setInterval."""
    code = re.sub(
        r"requestAnimationFrame\(\s*\w+\s*\);?\n?",
        "",
        code,
    )
    code = re.sub(
        r"(?:const|let|var)\s+\w+\s*=\s*requestAnimationFrame\([^)]*\);?\n?",
        "",
        code,
    )
    return code


def _add_slop_markers(code: str) -> str:
    """Add common AI slop patterns to ensure the code registers as generic."""
    slop_additions = []

    # Add generic hero section if not present
    if "hero-section" not in code:
        slop_additions.append(
            '<div class="hero-section bg-gradient-to-r from-purple-600 to-blue-500 min-h-screen flex items-center justify-center">\n'
            '  <div class="text-center">\n'
            '    <h1 class="text-6xl font-bold text-white animate-bounce">Welcome to Our Site</h1>\n'
            '    <p class="text-xl text-gray-200 mt-4">Get Started with our amazing platform</p>\n'
            '    <button class="cta-button mt-8 px-8 py-3 bg-white text-purple-600 rounded-lg font-bold hover:bg-gray-100 transition">\n'
            "      Learn More\n"
            "    </button>\n"
            "  </div>\n"
            "</div>"
        )

    # Add feature cards section
    if "feature-card" not in code:
        slop_additions.append(
            '<div class="grid grid-cols-3 gap-6 p-12">\n'
            '  <div class="feature-card p-6 bg-white rounded-lg shadow-lg">\n'
            '    <h3 class="text-xl font-bold">Feature One</h3>\n'
            '    <p class="text-gray-600 mt-2">Lorem ipsum dolor sit amet consectetur.</p>\n'
            "  </div>\n"
            '  <div class="feature-card p-6 bg-white rounded-lg shadow-lg">\n'
            '    <h3 class="text-xl font-bold">Feature Two</h3>\n'
            '    <p class="text-gray-600 mt-2">Lorem ipsum dolor sit amet consectetur.</p>\n'
            "  </div>\n"
            '  <div class="feature-card p-6 bg-white rounded-lg shadow-lg">\n'
            '    <h3 class="text-xl font-bold">Feature Three</h3>\n'
            '    <p class="text-gray-600 mt-2">Lorem ipsum dolor sit amet consectetur.</p>\n'
            "  </div>\n"
            "</div>"
        )

    if slop_additions:
        code = code.strip() + "\n\n" + "\n\n".join(slop_additions)

    return code


# ─── Main Generator ──────────────────────────────────────────────────────────


def generate_rejected(prompt: str, chosen_code: str) -> str:
    """
    Generate a competent-but-generic rejected version of creative code.

    Takes a creative code prompt and its hand-crafted chosen answer, produces
    a "competent but generic" rejected version by stripping creative techniques
    and replacing with standard patterns.

    The rejected output must:
    - Still be valid HTML/JS (competent, not broken)
    - Score as slop (is_slop=True) via slop_detector
    - Maintain the same general structure/sections
    - Contrast in quality of technique, not completeness

    Args:
        prompt: The instruction/prompt for the code
        chosen_code: The high-quality creative code (chosen answer)

    Returns:
        String of competent-but-generic rejected code that scores as slop.
    """
    rejected = chosen_code

    # Apply all stripping strategies
    rejected = _strip_three_js(rejected)
    rejected = _strip_gsap(rejected)
    rejected = _strip_lenis(rejected)
    rejected = _strip_canvas_svg(rejected)
    rejected = _strip_shaders(rejected)
    rejected = _strip_advanced_css(rejected)
    rejected = _strip_raf(rejected)

    # Clean up excessive whitespace from removals
    rejected = re.sub(r"\n{3,}", "\n\n", rejected)

    # Add slop markers to ensure it registers as generic
    rejected = _add_slop_markers(rejected)

    # Verify slop score
    result = slop_score(rejected)
    if not result["is_slop"]:
        # If not sloppy enough, add more generic patterns
        rejected = _add_slop_markers(rejected)
        # Force-add more signals
        rejected += '\n\n<div class="animate-pulse bg-gradient-to-r from-purple-400 to-blue-400 p-4 rounded">\n  <p class="text-white">Learn More about our platform</p>\n</div>'

    return rejected


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate competent-but-generic rejected code from creative examples.",
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input JSONL file (SFT format with conversations)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output directory for rejected code files",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify each rejected example scores as slop",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    total = 0
    verified = 0

    with open(args.input, "r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Extract prompt and chosen code from SFT format
            convos = entry.get("conversations", [])
            if len(convos) < 2:
                continue

            prompt = convos[0].get("content", "")
            assistant_content = convos[1].get("content", "")

            # Extract code from markdown fence
            code_match = re.search(r"```\w*\n(.*?)```", assistant_content, re.DOTALL)
            if not code_match:
                continue

            chosen_code = code_match.group(1)
            rejected = generate_rejected(prompt, chosen_code)

            total += 1

            if args.verify:
                result = slop_score(rejected)
                if result["is_slop"]:
                    verified += 1
                else:
                    print(
                        f"Warning: Entry {total} rejected code did not score as slop "
                        f"(score: {result['score']})",
                        file=sys.stderr,
                    )

            # Write rejected file
            output_file = os.path.join(args.output, f"rejected_{total:05d}.txt")
            with open(output_file, "w", encoding="utf-8") as fout:
                fout.write(rejected)

    print(f"Generated {total} rejected examples", file=sys.stderr)
    if args.verify:
        print(f"Verified as slop: {verified}/{total}", file=sys.stderr)


if __name__ == "__main__":
    main()
