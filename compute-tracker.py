#!/usr/bin/env python3
"""
KIN Compute Budget Tracker

Tracks compute unit consumption across all 6 companion training runs.
Prevents budget overruns and provides real-time estimates.

Usage:
    python compute-tracker.py status              # Show current budget
    python compute-tracker.py log cipher sft 45    # Log 45 units for cipher SFT
    python compute-tracker.py estimate forge grpo  # Estimate remaining cost
    python compute-tracker.py schedule             # Show 5-day plan
    python compute-tracker.py report               # Full report

Data stored in: training/output/compute-log.json
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# Constants
# ============================================================================

LOG_FILE = Path("training/output/compute-log.json")
TOTAL_BUDGET = 1100  # Pro+ 600 + PAYG 500

COMPANIONS = {
    "cipher":   {"emoji": "🐙", "name": "Cipher — Code Kraken"},
    "forge":    {"emoji": "🦄", "name": "Forge — Cyber Unicorn"},
    "vortex":   {"emoji": "🐉", "name": "Vortex — Teal Dragon"},
    "mischief": {"emoji": "🐕", "name": "Mischief — Glitch Pup"},
    "aether":   {"emoji": "🦍", "name": "Aether — Frost Ape"},
    "catalyst": {"emoji": "🫧", "name": "Catalyst — Cosmic Blob"},
}

# Estimated compute units per stage (Gemma 4 31B on A100)
ESTIMATES = {
    "sft":    {"cipher": 53, "forge": 45, "vortex": 38, "mischief": 30, "aether": 38, "catalyst": 30},
    "simpo":  {"cipher": 30, "forge": 23, "vortex": 23, "mischief": 15, "aether": 23, "catalyst": 15},
    "grpo":   {"cipher": 60, "forge": 53, "vortex": 45, "mischief": 38, "aether": 45, "catalyst": 38},
    "export": {"cipher": 8,  "forge": 8,  "vortex": 8,  "mischief": 8,  "aether": 8,  "catalyst": 8},
}

STAGES = ["sft", "simpo", "grpo", "export"]

SCHEDULE = {
    "Day 1": {"date": "Apr 12", "companions": ["cipher (SFT+SimPO)"], "est": 83},
    "Day 2": {"date": "Apr 13", "companions": ["cipher (GRPO+Export)", "forge (SFT+SimPO)"], "est": 136},
    "Day 3": {"date": "Apr 14", "companions": ["forge (GRPO+Export)", "vortex (full)"], "est": 175},
    "Day 4": {"date": "Apr 15", "companions": ["mischief (full)", "aether (full)"], "est": 205},
    "Day 5": {"date": "Apr 16", "companions": ["catalyst (full)", "eval all", "push to hub"], "est": 121},
}

# ============================================================================
# Data Management
# ============================================================================

def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return {"entries": [], "total_used": 0, "started": datetime.now().isoformat()}

def save_log(data):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(data, indent=2))

# ============================================================================
# Commands
# ============================================================================

def cmd_status():
    log = load_log()
    used = log["total_used"]
    remaining = TOTAL_BUDGET - used
    pct = (used / TOTAL_BUDGET) * 100

    print(f"\n{'='*55}")
    print(f"  KIN Training Budget Tracker")
    print(f"{'='*55}")
    print(f"  Budget:    {TOTAL_BUDGET} compute units")
    print(f"  Used:      {used} units ({pct:.1f}%)")
    print(f"  Remaining: {remaining} units")
    print(f"  {'='*51}")

    # Progress bar
    bar_len = 40
    filled = int(bar_len * used / TOTAL_BUDGET)
    bar = "█" * filled + "░" * (bar_len - filled)
    color = "\033[32m" if pct < 70 else "\033[33m" if pct < 90 else "\033[31m"
    print(f"  [{color}{bar}\033[0m] {pct:.1f}%")
    print()

    # Per-companion breakdown
    companion_usage = {}
    for entry in log["entries"]:
        cid = entry["companion"]
        companion_usage.setdefault(cid, {"total": 0, "stages": {}})
        companion_usage[cid]["total"] += entry["units"]
        companion_usage[cid]["stages"][entry["stage"]] = entry["units"]

    print(f"  {'Companion':<25} {'Used':>8} {'Est Total':>10} {'Status':>10}")
    print(f"  {'-'*53}")

    for cid, info in COMPANIONS.items():
        usage = companion_usage.get(cid, {"total": 0, "stages": {}})
        est_total = sum(ESTIMATES[s].get(cid, 0) for s in STAGES)
        completed_stages = list(usage.get("stages", {}).keys())
        remaining_stages = [s for s in STAGES if s not in completed_stages]

        if not remaining_stages:
            status = "✅ DONE"
        elif completed_stages:
            status = f"⏳ {remaining_stages[0].upper()}"
        else:
            status = "⬜ PENDING"

        print(f"  {info['emoji']} {info['name']:<22} {usage['total']:>6}u {est_total:>8}u {status:>10}")

    print()

def cmd_log(companion, stage, units):
    if companion not in COMPANIONS:
        print(f"Unknown companion: {companion}. Options: {', '.join(COMPANIONS.keys())}")
        sys.exit(1)
    if stage not in STAGES + ["eval", "other"]:
        print(f"Unknown stage: {stage}. Options: {', '.join(STAGES)}, eval, other")
        sys.exit(1)

    log = load_log()
    entry = {
        "companion": companion,
        "stage": stage,
        "units": units,
        "timestamp": datetime.now().isoformat(),
    }
    log["entries"].append(entry)
    log["total_used"] += units
    save_log(log)

    remaining = TOTAL_BUDGET - log["total_used"]
    emoji = COMPANIONS[companion]["emoji"]
    print(f"\n  {emoji} Logged {units} units for {companion} {stage.upper()}")
    print(f"  Remaining budget: {remaining} / {TOTAL_BUDGET} units\n")

def cmd_estimate(companion=None, stage=None):
    log = load_log()
    used = log["total_used"]

    if companion and stage:
        est = ESTIMATES.get(stage, {}).get(companion, 0)
        print(f"\n  Estimated: {est} units for {companion} {stage.upper()}")
        print(f"  After: {used + est} / {TOTAL_BUDGET} units used")
    else:
        total_est = sum(
            ESTIMATES[s].get(c, 0)
            for c in COMPANIONS
            for s in STAGES
        )
        print(f"\n  Total estimated for all 6 companions: {total_est} units")
        print(f"  Already used: {used} units")
        print(f"  Remaining estimate: {total_est - used} units")
        print(f"  Budget headroom: {TOTAL_BUDGET - total_est} units")
    print()

def cmd_schedule():
    log = load_log()
    used = log["total_used"]

    print(f"\n{'='*60}")
    print(f"  5-Day Training Schedule — All 6 KIN Companions")
    print(f"  Model: Gemma 4 31B | GPU: A100 | Budget: {TOTAL_BUDGET}u")
    print(f"{'='*60}\n")

    cumulative = 0
    for day, info in SCHEDULE.items():
        cumulative += info["est"]
        status = "✅" if cumulative <= used else "⬜"
        print(f"  {status} {day} ({info['date']}): ~{info['est']}u")
        for c in info["companions"]:
            print(f"       • {c}")
        print(f"       Running total: {cumulative}u / {TOTAL_BUDGET}u")
        print()

    print(f"  Total estimated: {cumulative}u")
    print(f"  Budget buffer:   {TOTAL_BUDGET - cumulative}u ({((TOTAL_BUDGET-cumulative)/TOTAL_BUDGET*100):.0f}% headroom)")
    print()

def cmd_report():
    cmd_status()
    cmd_schedule()
    cmd_estimate()

# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="KIN Compute Budget Tracker")
    parser.add_argument("command", choices=["status", "log", "estimate", "schedule", "report", "reset"])
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "log":
        if len(args.args) != 3:
            print("Usage: compute-tracker.py log <companion> <stage> <units>")
            sys.exit(1)
        cmd_log(args.args[0], args.args[1], int(args.args[2]))
    elif args.command == "estimate":
        companion = args.args[0] if len(args.args) > 0 else None
        stage = args.args[1] if len(args.args) > 1 else None
        cmd_estimate(companion, stage)
    elif args.command == "schedule":
        cmd_schedule()
    elif args.command == "report":
        cmd_report()
    elif args.command == "reset":
        save_log({"entries": [], "total_used": 0, "started": datetime.now().isoformat()})
        print("Budget tracker reset.")

if __name__ == "__main__":
    main()
