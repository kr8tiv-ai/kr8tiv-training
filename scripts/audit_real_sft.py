"""Audit the real-data Cipher SFT corpus for source-backed code only.

This is the fast sanity check we should run before retraining v3:
  - counts records by source
  - verifies every assistant payload is either full HTML or a real code module
  - rejects Aura shell metadata from being treated as assistant completions
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prompts" / "cipher-real-v1-sft.jsonl"


def classify_payload(text: str) -> str:
    low = text.lower()
    if "<!doctype" in low or "<html" in low:
        return "html"
    if "import " in text or "export " in text:
        return "module"
    return "suspicious"


def main() -> None:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_source: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    suspicious: list[tuple[int, str, str]] = []

    for idx, row in enumerate(rows, start=1):
        by_source[row.get("source", "unknown")] += 1
        assistant = next(
            (m.get("content", "") for m in row.get("messages", []) if m.get("role") == "assistant"),
            "",
        )
        kind = classify_payload(assistant)
        by_kind[kind] += 1
        if kind == "suspicious":
            suspicious.append((idx, row.get("source", "unknown"), assistant[:160].replace("\n", " ")))

    print(f"Dataset: {DATA}")
    print(f"Records: {len(rows)}")
    print(f"Sources: {dict(by_source)}")
    print(f"Payload kinds: {dict(by_kind)}")

    if suspicious:
        print("\nSuspicious rows:")
        for idx, source, preview in suspicious[:25]:
            print(f"  #{idx} [{source}] {preview}")
        raise SystemExit(f"Found {len(suspicious)} suspicious assistant payloads.")

    print("\nOK: every assistant payload is source-backed HTML or real code.")


if __name__ == "__main__":
    main()
