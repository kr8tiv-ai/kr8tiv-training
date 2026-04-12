#!/usr/bin/env python3
"""
Anti-Slop Pattern Detector for Cipher Code Kraken Training Data.

Scores code for "AI slop" signals -- generic template patterns, div soup,
gradient heroes, missing interactivity, utility-class-only styling.
Also provides a GRPO-compatible reward function.

Usage as module:
    from scripts.slop_detector import slop_score, creative_code_reward

Usage as CLI:
    python scripts/slop_detector.py --input code_sample.html
    echo '<div class="hero-section bg-gradient-to-r">...</div>' | python scripts/slop_detector.py
"""

import argparse
import re
import sys


# ─── Slop Detection Patterns ─────────────────────────────────────────────────

# Negative signals: each ADDS to slop score (higher = more sloppy)
NEGATIVE_SIGNALS = {
    # Div soup: >70% of HTML elements are <div>
    "div_soup": {
        "description": "Div soup (>70% div elements)",
        "weight": 3.0,
        "type": "structural",
    },
    # Gradient hero patterns
    "gradient_hero": {
        "patterns": [r"bg-gradient-to", r"from-purple", r"to-blue"],
        "description": "Gradient hero pattern",
        "weight": 2.0,
        "type": "pattern",
    },
    # Template naming
    "template_naming": {
        "patterns": [r"hero-section", r"cta-button", r"feature-card"],
        "description": "Template naming convention",
        "weight": 2.0,
        "type": "pattern",
    },
    # Generic copy
    "generic_copy": {
        "patterns": [r"Welcome to", r"Get Started", r"Learn More", r"Lorem ipsum"],
        "description": "Generic placeholder copy",
        "weight": 2.0,
        "type": "pattern",
    },
    # Missing interactivity
    "no_interactivity": {
        "description": "No addEventListener, gsap, THREE, Lenis, or requestAnimationFrame",
        "weight": 3.0,
        "type": "absence",
    },
    # Utility-class-only styling
    "utility_only": {
        "description": "No custom CSS (@keyframes, clip-path, mix-blend-mode, transform:, custom properties)",
        "weight": 2.0,
        "type": "absence",
    },
    # No canvas/WebGL/SVG
    "no_creative_elements": {
        "patterns": [r"<canvas", r"<svg", r"WebGL", r"gl_"],
        "description": "No canvas, SVG, WebGL, or GL usage",
        "weight": 2.0,
        "type": "absence",
    },
    # Bounce/pulse animations (Tailwind defaults)
    "tailwind_animations": {
        "patterns": [r"animate-bounce", r"animate-pulse"],
        "description": "Generic Tailwind animation classes",
        "weight": 2.0,
        "type": "pattern",
    },
}

# Positive signals: each SUBTRACTS from slop score (creative code indicators)
POSITIVE_SIGNALS = {
    "threejs": {
        "patterns": [r"THREE\.", r"from\s+['\"]three['\"]", r"import.*three"],
        "description": "Three.js usage",
        "weight": -2.0,
    },
    "gsap": {
        "patterns": [r"gsap\.", r"ScrollTrigger"],
        "description": "GSAP animation library",
        "weight": -2.0,
    },
    "lenis": {
        "patterns": [r"Lenis", r"lenis"],
        "description": "Lenis smooth scroll",
        "weight": -1.5,
    },
    "raf": {
        "patterns": [r"requestAnimationFrame"],
        "description": "requestAnimationFrame usage",
        "weight": -1.0,
    },
    "shaders": {
        "patterns": [r"gl_FragColor", r"shader"],
        "description": "WebGL shaders",
        "weight": -2.0,
    },
    "advanced_css": {
        "patterns": [r"clip-path", r"mix-blend-mode"],
        "description": "Advanced CSS techniques",
        "weight": -1.5,
    },
    "intersection_observer": {
        "patterns": [r"IntersectionObserver"],
        "description": "IntersectionObserver API",
        "weight": -1.0,
    },
    "canvas": {
        "patterns": [r"canvas"],
        "description": "Canvas usage",
        "weight": -1.0,
    },
    "code_length_50": {
        "description": "Code length > 50 lines",
        "weight": -1.0,
        "type": "structural",
    },
    "code_length_150": {
        "description": "Code length > 150 lines",
        "weight": -1.0,
        "type": "structural",
    },
}

# Threshold: above this score, code is classified as slop
SLOP_THRESHOLD = 5.0


# ─── Core Detection ──────────────────────────────────────────────────────────


def _count_elements(code: str) -> dict:
    """Count HTML elements in code for structural analysis."""
    element_tags = [
        "div", "section", "article", "canvas", "svg",
        "main", "header", "nav", "footer", "aside",
        "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "a", "img", "figure", "figcaption",
        "form", "input", "button", "table", "video", "audio",
    ]
    counts = {}
    for tag in element_tags:
        counts[tag] = len(re.findall(rf"<{tag}[\s>]", code, re.IGNORECASE))
    return counts


def _has_interactivity(code: str) -> bool:
    """Check if code contains any interactive JS patterns."""
    interactive_patterns = [
        "addEventListener",
        "gsap",
        "THREE",
        "Lenis",
        "requestAnimationFrame",
    ]
    return any(pattern in code for pattern in interactive_patterns)


def _has_custom_css(code: str) -> bool:
    """Check if code contains custom CSS beyond utility classes."""
    custom_patterns = [
        "@keyframes",
        "clip-path",
        "mix-blend-mode",
        "transform:",
        "--",  # CSS custom properties
    ]
    return any(pattern in code for pattern in custom_patterns)


def _has_creative_elements(code: str) -> bool:
    """Check if code contains canvas, SVG, WebGL, or GL elements."""
    patterns = ["<canvas", "<svg", "WebGL", "gl_"]
    return any(pattern in code for pattern in patterns)


def slop_score(code: str) -> dict:
    """
    Score code for AI slop patterns.

    Args:
        code: Source code string (HTML, CSS, JS, or combined)

    Returns:
        {
            "score": float,       # Total slop score (higher = more slop)
            "signals": list[str], # Human-readable signal descriptions
            "is_slop": bool       # True if score > SLOP_THRESHOLD
        }
    """
    score = 0.0
    signals = []

    # ── Negative signals (add to score) ──

    # Div soup detection
    element_counts = _count_elements(code)
    div_count = element_counts.get("div", 0)
    total_elements = sum(element_counts.values())
    if total_elements > 0 and div_count / total_elements > 0.7:
        score += NEGATIVE_SIGNALS["div_soup"]["weight"]
        signals.append(f"+{NEGATIVE_SIGNALS['div_soup']['weight']}: {NEGATIVE_SIGNALS['div_soup']['description']} ({div_count}/{total_elements} elements)")

    # Pattern-based negative signals
    for key in ["gradient_hero", "template_naming", "generic_copy", "tailwind_animations"]:
        signal = NEGATIVE_SIGNALS[key]
        for pattern in signal["patterns"]:
            if re.search(pattern, code):
                score += signal["weight"]
                signals.append(f"+{signal['weight']}: {signal['description']} (matched: {pattern})")

    # Absence-based negative signals
    if not _has_interactivity(code):
        sig = NEGATIVE_SIGNALS["no_interactivity"]
        score += sig["weight"]
        signals.append(f"+{sig['weight']}: {sig['description']}")

    if not _has_custom_css(code):
        sig = NEGATIVE_SIGNALS["utility_only"]
        score += sig["weight"]
        signals.append(f"+{sig['weight']}: {sig['description']}")

    if not _has_creative_elements(code):
        sig = NEGATIVE_SIGNALS["no_creative_elements"]
        score += sig["weight"]
        signals.append(f"+{sig['weight']}: {sig['description']}")

    # ── Positive signals (subtract from score) ──

    for key, signal in POSITIVE_SIGNALS.items():
        if key == "code_length_50":
            if code.count("\n") > 50:
                score += signal["weight"]
                signals.append(f"{signal['weight']}: {signal['description']}")
            continue
        if key == "code_length_150":
            if code.count("\n") > 150:
                score += signal["weight"]
                signals.append(f"{signal['weight']}: {signal['description']}")
            continue

        for pattern in signal.get("patterns", []):
            if re.search(pattern, code):
                score += signal["weight"]
                signals.append(f"{signal['weight']}: {signal['description']} (matched: {pattern})")
                break  # Only count each positive signal category once

    return {
        "score": round(score, 1),
        "signals": signals,
        "is_slop": score > SLOP_THRESHOLD,
    }


def creative_code_reward(completions: list[str], **kwargs) -> list[float]:
    """
    GRPO-compatible reward function for creative code quality.

    Takes a list of completion strings, returns a list of reward scores.
    Positive rewards for creative code, negative for AI slop.
    This function is used directly by the GRPO trainer.

    Args:
        completions: List of generated code strings
        **kwargs: Additional keyword args (ignored, for GRPO compatibility)

    Returns:
        List of float reward scores (higher = better creative code)
    """
    rewards = []
    for completion in completions:
        result = slop_score(completion)
        # Negate the slop score: low slop = high reward, high slop = low reward
        # Shift so that creative code gets positive rewards
        reward = -result["score"]
        rewards.append(reward)
    return rewards


# ─── CLI ──────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score code for AI slop patterns. Positive score = sloppy, negative = creative.",
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input file to score (reads from stdin if not provided)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SLOP_THRESHOLD,
        help=f"Slop threshold (default: {SLOP_THRESHOLD})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of human-readable format",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        code = sys.stdin.read()

    result = slop_score(code)

    if args.json:
        import json

        print(json.dumps(result, indent=2))
    else:
        print(f"Slop Score: {result['score']}")
        print(f"Is Slop: {result['is_slop']}")
        print(f"\nSignals ({len(result['signals'])}):")
        for signal in result["signals"]:
            print(f"  {signal}")


if __name__ == "__main__":
    main()
