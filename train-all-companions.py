#!/usr/bin/env python3
"""
KIN Master Training Script — Train All 6 Companions

Orchestrates the full 4-stage pipeline for each companion:
SFT → SimPO → GRPO → GGUF Export → Push to Hub

Supports both Gemma 4 E4B (T4/free) and 31B (A100/Pro+).
Includes compute budget tracking and checkpoint resumption.

Usage:
    # Train all 6 on 31B (A100 — Colab Pro+)
    python train-all-companions.py --model 31b --all

    # Train specific companion
    python train-all-companions.py --model 31b --companion cipher

    # Resume from checkpoint (if Colab disconnects)
    python train-all-companions.py --model 31b --resume

    # Train on E4B (T4 — free tier)
    python train-all-companions.py --model e4b --all

    # Dry run (estimate compute only)
    python train-all-companions.py --model 31b --all --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# Model Configs
# ============================================================================

MODELS = {
    "31b": {
        "hf_id": "unsloth/gemma-4-31B-it-bnb-4bit",
        "family": "gemma",
        "lora_rank": 64,
        "lora_alpha": 128,
        "max_seq_length": 8192,
        "sft_lr": 2e-4,
        "sft_batch": 1,
        "sft_grad_accum": 16,
        "gpu_required": "A100",
        "vram_gb": 40,
    },
    "e4b": {
        "hf_id": "unsloth/gemma-4-E4B-it-bnb-4bit",
        "family": "gemma",
        "lora_rank": 32,
        "lora_alpha": 64,
        "max_seq_length": 4096,
        "sft_lr": 2e-4,
        "sft_batch": 2,
        "sft_grad_accum": 8,
        "gpu_required": "T4",
        "vram_gb": 15,
    },
}

COMPANIONS = ["cipher", "forge", "vortex", "mischief", "aether", "catalyst"]

COMPANION_INFO = {
    "cipher":   {"emoji": "🐙", "name": "Code Kraken",   "sft": 8000, "simpo": 5000, "grpo": 3000},
    "forge":    {"emoji": "🦄", "name": "Cyber Unicorn",  "sft": 7000, "simpo": 4000, "grpo": 2500},
    "vortex":   {"emoji": "🐉", "name": "Teal Dragon",    "sft": 6000, "simpo": 3500, "grpo": 2000},
    "mischief": {"emoji": "🐕", "name": "Glitch Pup",     "sft": 5000, "simpo": 3000, "grpo": 1500},
    "aether":   {"emoji": "🦍", "name": "Frost Ape",      "sft": 6000, "simpo": 3500, "grpo": 2000},
    "catalyst": {"emoji": "🫧", "name": "Cosmic Blob",    "sft": 5000, "simpo": 3000, "grpo": 1500},
}

CHECKPOINT_FILE = Path("training/output/training-checkpoint.json")

# ============================================================================
# Checkpoint Management
# ============================================================================

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"completed": {}, "current": None, "started": datetime.now().isoformat()}

def save_checkpoint(data):
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(data, indent=2))

def mark_complete(companion, stage):
    cp = load_checkpoint()
    cp["completed"].setdefault(companion, [])
    if stage not in cp["completed"][companion]:
        cp["completed"][companion].append(stage)
    cp["current"] = None
    save_checkpoint(cp)

def is_complete(companion, stage):
    cp = load_checkpoint()
    return stage in cp["completed"].get(companion, [])

def set_current(companion, stage):
    cp = load_checkpoint()
    cp["current"] = {"companion": companion, "stage": stage, "started": datetime.now().isoformat()}
    save_checkpoint(cp)

# ============================================================================
# Training Stages
# ============================================================================

def run_stage(companion, stage, model_config, dry_run=False):
    """Run a single training stage for a companion."""
    info = COMPANION_INFO[companion]
    emoji = info["emoji"]

    if is_complete(companion, stage):
        print(f"  {emoji} {companion} {stage.upper()} — already complete, skipping")
        return True

    print(f"\n{'='*60}")
    print(f"  {emoji} {companion.upper()} — Stage: {stage.upper()}")
    print(f"  Model: {model_config['hf_id']}")
    print(f"{'='*60}\n")

    if dry_run:
        print(f"  [DRY RUN] Would train {companion} {stage}")
        return True

    set_current(companion, stage)

    # Build command based on stage
    base_model = model_config["hf_id"]
    output_dir = f"training/output/{companion}/{stage}"
    data_dir = f"data/training/{companion}"

    # Check if previous stage output exists (use as base)
    prev_stages = {"simpo": "sft", "grpo": "simpo"}
    if stage in prev_stages:
        prev_output = f"training/output/{companion}/{prev_stages[stage]}/lora"
        if Path(prev_output).exists():
            base_model = prev_output

    common_args = [
        f"--base-model={base_model}",
        f"--output-dir={output_dir}",
        f"--lora-rank={model_config['lora_rank']}",
        f"--lora-alpha={model_config['lora_alpha']}",
    ]

    if stage == "sft":
        cmd = [
            sys.executable, "companions/cipher/training/stage1-sft/train.py",
            f"--data-dir={data_dir}",
            f"--epochs=2",
            f"--batch-size={model_config['sft_batch']}",
            f"--grad-accum={model_config['sft_grad_accum']}",
            f"--lr={model_config['sft_lr']}",
            f"--max-seq-length={model_config['max_seq_length']}",
        ] + common_args

    elif stage == "simpo":
        cmd = [
            sys.executable, "companions/cipher/training/stage2-simpo/train.py",
            f"--data-path={data_dir}/preference-pairs.jsonl",
        ] + common_args

    elif stage == "grpo":
        cmd = [
            sys.executable, "companions/cipher/training/stage3-grpo/train.py",
            f"--data-path={data_dir}/grpo-problems.jsonl",
            "--reward-mode=text",
        ] + common_args

    elif stage == "export":
        # GGUF export is handled in the last training stage
        print(f"  {emoji} Exporting GGUF for {companion}...")
        mark_complete(companion, stage)
        return True

    print(f"  Running: {' '.join(cmd[:3])}...")
    start = time.time()

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        elapsed = time.time() - start
        print(f"\n  {emoji} {companion} {stage.upper()} complete! ({elapsed/60:.1f} min)")

        # Log compute units
        units = int(elapsed / 60 * 15 / 60)  # Rough: 15 units/hour on A100
        try:
            subprocess.run([
                sys.executable, "training/compute-tracker.py",
                "log", companion, stage, str(units)
            ], check=False)
        except Exception:
            pass

        mark_complete(companion, stage)
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n  ❌ {companion} {stage.upper()} FAILED: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n  ⏸️  Training interrupted. Resume with --resume")
        return False

# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="KIN Master Training — All 6 Companions")
    parser.add_argument("--model", choices=["31b", "e4b"], default="31b")
    parser.add_argument("--companion", choices=COMPANIONS, help="Train single companion")
    parser.add_argument("--all", action="store_true", help="Train all 6 companions")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Estimate compute only")
    parser.add_argument("--stage", choices=["sft", "simpo", "grpo", "export"], help="Run specific stage only")
    parser.add_argument("--push-to-hub", action="store_true", help="Push GGUF to HuggingFace")
    args = parser.parse_args()

    model_config = MODELS[args.model]
    stages = [args.stage] if args.stage else ["sft", "simpo", "grpo", "export"]

    # Determine which companions to train
    if args.companion:
        companions = [args.companion]
    elif args.all or args.resume:
        companions = COMPANIONS
    else:
        print("Specify --companion <name> or --all")
        sys.exit(1)

    # Header
    print(f"\n{'='*60}")
    print(f"  🐙🦄🐉🐕🦍🫧  KIN Training Pipeline")
    print(f"  Model: Gemma 4 {args.model.upper()} | GPU: {model_config['gpu_required']}")
    print(f"  Companions: {', '.join(companions)}")
    print(f"  Stages: {' → '.join(s.upper() for s in stages)}")
    if args.dry_run:
        print(f"  MODE: DRY RUN")
    print(f"{'='*60}\n")

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / 1e9
            print(f"  GPU: {gpu_name} ({vram:.1f} GB)")
            if vram < model_config["vram_gb"]:
                print(f"  ⚠️  WARNING: {args.model.upper()} needs {model_config['vram_gb']}GB, you have {vram:.1f}GB")
                if args.model == "31b":
                    print(f"  Falling back to E4B...")
                    model_config = MODELS["e4b"]
        else:
            print("  ⚠️  No GPU detected!")
    except ImportError:
        print("  ⚠️  PyTorch not installed — install with: pip install torch")

    # Run training
    success_count = 0
    fail_count = 0

    for companion in companions:
        info = COMPANION_INFO[companion]
        print(f"\n{'─'*60}")
        print(f"  {info['emoji']} Starting {companion.upper()} — {info['name']}")
        print(f"{'─'*60}")

        for stage in stages:
            ok = run_stage(companion, stage, model_config, args.dry_run)
            if ok:
                success_count += 1
            else:
                fail_count += 1
                if not args.dry_run:
                    print(f"\n  ⚠️  {companion} {stage} failed. Continuing with next...")

    # Summary
    print(f"\n{'='*60}")
    print(f"  TRAINING COMPLETE")
    print(f"  ✅ Succeeded: {success_count}")
    if fail_count:
        print(f"  ❌ Failed: {fail_count}")
    print(f"{'='*60}\n")

    # Show budget
    try:
        subprocess.run([sys.executable, "training/compute-tracker.py", "status"], check=False)
    except Exception:
        pass


if __name__ == "__main__":
    main()
