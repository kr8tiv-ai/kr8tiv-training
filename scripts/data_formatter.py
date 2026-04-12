#!/usr/bin/env python3
"""
Training Data Formatter for Cipher Code Kraken.

Converts raw scraped code entries into the 4 training dataset formats:
- SFT: Chat-template instruction-response pairs
- SimPO: Chosen/rejected preference pairs
- GRPO: Prompt-only for reward-guided generation
- KTO: Prompt + completion + binary label

Usage as module:
    from scripts.data_formatter import format_sft, format_simpo, format_grpo, format_kto

Usage as CLI:
    python scripts/data_formatter.py --input data/raw/github.jsonl --output data/prompts/sft_prompts.jsonl --format sft
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Optional


# ─── Library/Technique Detection ──────────────────────────────────────────────

LIBRARY_DETECTORS = {
    "Three.js": [r"THREE\.", r"from\s+['\"]three['\"]", r"import.*three", r"BufferGeometry", r"Scene\(\)", r"Mesh\("],
    "GSAP": [r"gsap\.", r"gsap\.to\(", r"gsap\.from\(", r"gsap\.timeline", r"ScrollTrigger", r"SplitText"],
    "Lenis": [r"Lenis", r"lenis"],
    "WebGL": [r"WebGL", r"gl_FragColor", r"gl_Position", r"shader", r"vertexShader", r"fragmentShader"],
    "Canvas": [r"getContext\(['\"]2d", r"getContext\(['\"]webgl", r"<canvas"],
    "SVG Animation": [r"<svg", r"animate\(", r"animateTransform", r"svg\."],
    "Framer Motion": [r"motion\.", r"useSpring", r"AnimatePresence", r"framer-motion"],
    "CSS Advanced": [r"clip-path", r"mix-blend-mode", r"@keyframes", r"transform:", r"perspective:"],
    "IntersectionObserver": [r"IntersectionObserver"],
    "Vanilla JS Interactions": [r"requestAnimationFrame", r"addEventListener.*mouse", r"addEventListener.*scroll"],
}

TECHNIQUE_DETECTORS = {
    "particle system": [r"particle", r"BufferGeometry.*position", r"points"],
    "scroll animation": [r"ScrollTrigger", r"scroll.*trigger", r"onscroll", r"IntersectionObserver"],
    "smooth scrolling": [r"Lenis", r"smooth.*scroll", r"scroll-behavior"],
    "3D scene": [r"Scene\(\)", r"PerspectiveCamera", r"OrbitControls", r"Mesh\("],
    "shader effect": [r"gl_FragColor", r"shader", r"vertexShader", r"fragmentShader", r"uniform"],
    "text animation": [r"SplitText", r"text.*reveal", r"letter.*anim", r"char.*anim"],
    "cursor effect": [r"cursor", r"mousemove.*custom", r"pointer.*follow"],
    "parallax": [r"parallax", r"translate.*scroll", r"scrollY.*transform"],
    "page transition": [r"page.*transition", r"route.*transition", r"Flip", r"layout.*anim"],
    "hover effect": [r"mouseenter", r"mouseleave", r"hover.*effect", r"magnetic"],
    "canvas experiment": [r"getContext\(['\"]2d", r"canvas.*draw", r"fillRect", r"arc\("],
    "WebGL experiment": [r"WebGLRenderer", r"getContext\(['\"]webgl"],
    "clip-path animation": [r"clip-path.*polygon", r"clip-path.*circle", r"clip-path.*inset"],
    "blend mode effect": [r"mix-blend-mode", r"blend.*mode"],
    "loading animation": [r"loader", r"preload", r"progress.*bar.*anim"],
}


def detect_libraries(code: str) -> list[str]:
    """Detect which creative libraries are used in the code."""
    found = []
    for lib, patterns in LIBRARY_DETECTORS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                found.append(lib)
                break
    return found


def detect_techniques(code: str) -> list[str]:
    """Detect which creative techniques are demonstrated in the code."""
    found = []
    for technique, patterns in TECHNIQUE_DETECTORS.items():
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                found.append(technique)
                break
    return found


def generate_instruction(code: str, libraries: list[str], techniques: list[str]) -> str:
    """
    Generate a natural language instruction from detected libraries and techniques.
    This creates the 'user' turn for the SFT chat template.
    """
    if not libraries and not techniques:
        return "Create an interactive web component with custom animations and creative visual effects."

    # Build instruction from detected context
    parts = []

    if techniques:
        primary_technique = techniques[0]
        parts.append(f"Create a {primary_technique}")

        if len(techniques) > 1:
            secondary = techniques[1:3]  # Max 2 additional
            parts.append(f" with {' and '.join(secondary)}")

    if libraries:
        lib_str = ", ".join(libraries[:3])
        if parts:
            parts.append(f" using {lib_str}")
        else:
            parts.append(f"Build an interactive component using {lib_str}")

    # Add specificity based on detected patterns
    specifics = []
    if "Three.js" in libraries:
        if "particle system" in techniques:
            specifics.append("with dynamic particle positioning and organic movement")
        elif "3D scene" in techniques:
            specifics.append("with camera controls and responsive viewport handling")
        elif "shader effect" in techniques:
            specifics.append("with custom GLSL shaders for visual effects")
    if "GSAP" in libraries:
        if "scroll animation" in techniques:
            specifics.append("with scroll-triggered timeline sequences")
        elif "text animation" in techniques:
            specifics.append("with staggered text reveal animations")
    if "Lenis" in libraries:
        specifics.append("with buttery smooth scroll integration")

    if specifics:
        parts.append(f" {specifics[0]}")

    instruction = "".join(parts)

    # Ensure it ends with proper punctuation
    if not instruction.endswith("."):
        instruction += "."

    return instruction


def generate_explanation(code: str, libraries: list[str], techniques: list[str]) -> str:
    """
    Generate a brief explanation of key techniques used in the code.
    This follows the code block in the assistant response.
    """
    explanations = []

    if "Three.js" in libraries:
        explanations.append("Three.js scene setup with proper renderer, camera, and animation loop")
    if "GSAP" in libraries:
        explanations.append("GSAP timeline with ScrollTrigger for scroll-linked animations")
    if "Lenis" in libraries:
        explanations.append("Lenis smooth scrolling with RAF-synced updates")
    if "WebGL" in libraries:
        explanations.append("Custom GLSL shaders for GPU-accelerated visual effects")
    if "Canvas" in libraries:
        explanations.append("HTML5 Canvas with optimized draw calls and animation frame management")
    if "CSS Advanced" in libraries:
        explanations.append("Advanced CSS with clip-path, blend modes, and custom property animations")
    if "IntersectionObserver" in libraries:
        explanations.append("IntersectionObserver for performant viewport detection")

    if not explanations:
        explanations.append("Custom interactive component with hand-crafted animations")

    parts = ["Key techniques:"]
    for exp in explanations[:4]:
        parts.append(f"- {exp}")

    return "\n".join(parts)


def line_count(text: str) -> int:
    """Count non-empty lines."""
    return len([line for line in text.split("\n") if line.strip()])


def detect_language(content: str, file_path: str = "") -> str:
    """Detect the primary language for code fence."""
    ext = os.path.splitext(file_path)[1].lower() if file_path else ""
    if ext in (".ts", ".tsx"):
        return "typescript"
    if ext in (".jsx",):
        return "jsx"
    if ext == ".css":
        return "css"
    if "// === HTML ===" in content and "// === JS ===" in content:
        return "html"
    if "<template>" in content or "<script>" in content:
        return "html"
    return "javascript"


# ─── Format Functions ─────────────────────────────────────────────────────────


def format_sft(raw_entry: dict) -> Optional[dict]:
    """
    Convert a scraped entry into SFT chat-template format.

    Args:
        raw_entry: Dict with at least 'content' key, optionally 'file', 'repo', etc.

    Returns:
        {"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        or None if entry doesn't meet quality bar.
    """
    content = raw_entry.get("content", "")

    # Filter: minimum 50 lines for full component
    if line_count(content) < 50:
        return None

    # Detect context
    libraries = detect_libraries(content)
    techniques = detect_techniques(content)

    # Generate instruction
    instruction = generate_instruction(content, libraries, techniques)

    # Detect language for code fence
    lang = detect_language(content, raw_entry.get("file", ""))

    # Generate explanation
    explanation = generate_explanation(content, libraries, techniques)

    # Build assistant response: code + explanation
    assistant_content = f"```{lang}\n{content.strip()}\n```\n\n{explanation}"

    return {
        "conversations": [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def format_simpo(chosen_entry: dict, rejected_code: str) -> Optional[dict]:
    """
    Create a SimPO preference pair from a chosen entry and rejected code.

    Args:
        chosen_entry: Dict with 'content' key (high-quality creative code)
        rejected_code: String of competent-but-generic rejected code

    Returns:
        {"prompt": "...", "chosen": "...", "rejected": "..."}
        or None if inputs don't meet quality bar.
    """
    chosen_content = chosen_entry.get("content", "")

    if line_count(chosen_content) < 50:
        return None

    libraries = detect_libraries(chosen_content)
    techniques = detect_techniques(chosen_content)
    instruction = generate_instruction(chosen_content, libraries, techniques)

    lang = detect_language(chosen_content, chosen_entry.get("file", ""))

    chosen_explanation = generate_explanation(chosen_content, libraries, techniques)
    chosen_response = f"```{lang}\n{chosen_content.strip()}\n```\n\n{chosen_explanation}"

    rejected_response = f"```html\n{rejected_code.strip()}\n```\n\nThis implements the basic structure using standard HTML and CSS patterns."

    return {
        "prompt": instruction,
        "chosen": chosen_response,
        "rejected": rejected_response,
    }


def format_grpo(entry: dict) -> Optional[dict]:
    """
    Create a GRPO prompt-only entry for reward-guided generation.

    Args:
        entry: Dict with 'content' key

    Returns:
        {"prompt": "..."} or None if entry doesn't meet quality bar.
    """
    content = entry.get("content", "")

    if line_count(content) < 50:
        return None

    libraries = detect_libraries(content)
    techniques = detect_techniques(content)
    instruction = generate_instruction(content, libraries, techniques)

    return {"prompt": instruction}


def format_kto(entry: dict, label: bool) -> Optional[dict]:
    """
    Create a KTO binary-label entry.

    Args:
        entry: Dict with 'content' key
        label: True for thumbs-up (creative code), False for thumbs-down (slop)

    Returns:
        {"prompt": "...", "completion": "...", "label": true/false}
        or None if entry doesn't meet quality bar.
    """
    content = entry.get("content", "")

    if line_count(content) < 20:
        return None

    libraries = detect_libraries(content)
    techniques = detect_techniques(content)
    instruction = generate_instruction(content, libraries, techniques)

    lang = detect_language(content, entry.get("file", ""))
    completion = f"```{lang}\n{content.strip()}\n```"

    return {
        "prompt": instruction,
        "completion": completion,
        "label": label,
    }


# ─── Deduplication ────────────────────────────────────────────────────────────


def content_hash(content: str) -> str:
    """Generate a content hash for deduplication."""
    # Normalize whitespace before hashing
    normalized = re.sub(r"\s+", " ", content.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# ─── CLI Pipeline ─────────────────────────────────────────────────────────────


def process_file(input_path: str, output_path: str, fmt: str) -> None:
    """
    Process a raw JSONL file into formatted training data.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    seen_hashes = set()
    total_in = 0
    total_out = 0

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            total_in += 1

            # Deduplicate
            chash = content_hash(entry.get("content", ""))
            if chash in seen_hashes:
                continue
            seen_hashes.add(chash)

            # Format based on requested type
            formatted = None
            if fmt == "sft":
                formatted = format_sft(entry)
            elif fmt == "grpo":
                formatted = format_grpo(entry)
            elif fmt == "kto":
                # For CLI, default to label=True (quality entries)
                formatted = format_kto(entry, label=True)
            elif fmt == "simpo":
                # SimPO requires rejected code -- skip in simple CLI mode
                # (use the notebook pipeline for proper SimPO generation)
                print(
                    "Warning: SimPO format requires rejected code generation. "
                    "Use the notebook pipeline for proper SimPO dataset creation.",
                    file=sys.stderr,
                )
                formatted = format_grpo(entry)  # Fall back to prompt-only

            if formatted:
                fout.write(json.dumps(formatted, ensure_ascii=False) + "\n")
                total_out += 1

    print(f"Processed: {total_in} entries -> {total_out} formatted ({fmt})", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Format raw scraped code into training dataset formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formats:
  sft    - Chat-template instruction-response pairs
  simpo  - Preference pairs (requires notebook pipeline for rejected generation)
  grpo   - Prompt-only for reward-guided generation
  kto    - Prompt + completion + binary label

Examples:
  python scripts/data_formatter.py --input data/raw/github.jsonl --output data/prompts/sft_prompts.jsonl --format sft
  python scripts/data_formatter.py --input data/raw/codepen.jsonl --output data/prompts/grpo_prompts.jsonl --format grpo
        """,
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Input JSONL file (raw scraped data)"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output JSONL file (formatted training data)"
    )
    parser.add_argument(
        "--format",
        "-f",
        required=True,
        choices=["sft", "simpo", "grpo", "kto"],
        help="Output format: sft, simpo, grpo, kto",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_file(args.input, args.output, args.format)


if __name__ == "__main__":
    main()
