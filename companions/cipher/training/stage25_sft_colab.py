"""LEGACY: Cipher Stage 2.5 synthetic-data SFT on Awwwards-distilled gold data.

Paste this into a fresh Colab A100 cell. Loads cipher-simpo-merged (our
Stage 2 output), applies LoRA, and fine-tunes on 288 (prompt, completion)
pairs synthesized from the 96 SOTD patterns.

This file is preserved as historical reference only.
Use `stage25_real_sft_colab.py` for the real-data retrain that backs
`Auroraventures/cipher-sft25-real-merged`.

Why this is legacy:
  Stage 1 SFT taught Cipher to write clean HTML.
  Stage 2 SimPO killed the slop (Tailwind fallback, opacity cascade bug, etc.).
  This synthetic Stage 2.5 path taught the stack, but it also produced
  template collapse. The real-data v3 path supersedes it.
"""

# ==========================================================================
# Cell 1 — Install + auth
# ==========================================================================
INSTALL_CELL = r"""
# Install pinned versions (Colab base image updates can break compat)
!pip install -q -U "unsloth[cu121-ampere-torch240]==2026.3.2" \
    "transformers==4.47.1" "trl==0.13.0" "peft==0.14.0" \
    "datasets==3.0.0" "accelerate==1.2.1" "bitsandbytes==0.45.0"

from google.colab import userdata
import os

# Pull HF token from Colab Secrets (fallback to env)
for k in ("HF_TOKEN", "HUGGINGFACE_TOKEN", "HF_WRITE_TOKEN"):
    try:
        tok = userdata.get(k)
        if tok:
            os.environ["HF_TOKEN"] = tok
            break
    except Exception:
        continue

# Verify GPU
import subprocess
print(subprocess.check_output("nvidia-smi --query-gpu=name,memory.total --format=csv", shell=True).decode())
"""


# ==========================================================================
# Cell 2 — Load cipher-simpo-merged with LoRA
# ==========================================================================
LOAD_CELL = r"""
from unsloth import FastLanguageModel
import torch

MAX_SEQ = 6144   # fits an Awwwards-size completion + prompt
BASE = "Auroraventures/cipher-simpo-merged"   # Stage 2 output

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE,
    max_seq_length=MAX_SEQ,
    dtype=None,          # auto-detect bf16 on A100
    load_in_4bit=True,
    token=os.environ.get("HF_TOKEN"),
)

# Gemma 4 chat template already correct in unsloth -- verify
print("Chat template length:", len(tokenizer.chat_template) if tokenizer.chat_template else 0)

# Apply LoRA (same config we used for Stage 1/2, reduced rank for stability)
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=128,            # 2x ratio (paper-optimal for code)
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    use_rslora=True,           # rsLoRA for 31B stability
    random_state=3407,
)
print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
"""


# ==========================================================================
# Cell 3 — Load + format dataset
# ==========================================================================
DATA_CELL = r"""
# If you uploaded awwwards-stage25-sft.jsonl to /content or Google Drive:
DATA_PATH = "/content/awwwards-stage25-sft.jsonl"

# Or fetch from HF hub (if we upload it as a dataset)
# from datasets import load_dataset
# ds = load_dataset("Auroraventures/cipher-awwwards-sft25")["train"]

from datasets import load_dataset
ds = load_dataset("json", data_files=DATA_PATH, split="train")
print(f"Loaded {len(ds)} records")
print(f"Shape distribution: {ds.to_pandas()['shape'].value_counts().to_dict()}")

# Format messages into Gemma 4 prompt
def format_example(example):
    messages = example["messages"]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text}

ds = ds.map(format_example)

# Truncation check — make sure we fit in max_seq
lens = [len(tokenizer.encode(r["text"])) for r in ds.select(range(min(100, len(ds))))]
print(f"Token length sample: min={min(lens)} mean={sum(lens)//len(lens)} max={max(lens)}")
print(f"Records > MAX_SEQ: {sum(1 for l in lens if l > MAX_SEQ)}")
"""


# ==========================================================================
# Cell 4 — Train
# ==========================================================================
TRAIN_CELL = r"""
from trl import SFTTrainer, SFTConfig

# Train on ASSISTANT turns only (response masking) — critical to avoid
# learning to repeat the prompt.
from unsloth.chat_templates import train_on_responses_only

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ,
    args=SFTConfig(
        output_dir="outputs/cipher-sft25",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=16,     # Effective batch 32
        warmup_ratio=0.1,
        num_train_epochs=2,                  # 288 × 2 = 576 steps at bs=32 = ~18 steps
        learning_rate=5.0e-5,                # Lower than Stage 1 (we're refining)
        bf16=True,
        logging_steps=5,
        save_strategy="epoch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        report_to="none",
    ),
)

# Response-only masking: loss only flows through assistant tokens
trainer = train_on_responses_only(
    trainer,
    instruction_part="<start_of_turn>user\n",
    response_part="<start_of_turn>model\n",
)

print("Starting Stage 2.5 training...")
trainer_stats = trainer.train()
print(f"Finished. Final loss: {trainer_stats.training_loss:.4f}")
"""


# ==========================================================================
# Cell 5 — Save + push to HF
# ==========================================================================
SAVE_CELL = r"""
MERGED_REPO = "Auroraventures/cipher-sft25-merged"
GGUF_REPO   = "Auroraventures/cipher-sft25-merged-Q4_K_M-GGUF"

# Save LoRA adapter
model.save_pretrained("outputs/cipher-sft25-lora")
tokenizer.save_pretrained("outputs/cipher-sft25-lora")

# Merge + push
model.save_pretrained_merged("outputs/cipher-sft25-merged", tokenizer, save_method="merged_16bit")
print("Merged model saved. Pushing to HF...")

from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])
api.create_repo(MERGED_REPO, repo_type="model", private=False, exist_ok=True)
api.upload_folder(
    folder_path="outputs/cipher-sft25-merged",
    repo_id=MERGED_REPO,
    repo_type="model",
    commit_message="Stage 2.5 SFT on Awwwards-distilled gold (288 records)",
)
print(f"Pushed: https://huggingface.co/{MERGED_REPO}")
print(f"Next: use gguf-my-repo space to convert to {GGUF_REPO}")
"""


# ==========================================================================
# Cell 6 — Smoke test
# ==========================================================================
SMOKE_CELL = r"""
# Quick generation test on a new prompt
FastLanguageModel.for_inference(model)

SYSTEM = (
    "You are Cipher, the Code Kraken. Build COMPLETE Awwwards-quality single-file HTML. "
    "NO Tailwind. Vanilla CSS only. Only Three.js/GSAP/Lenis (CDN inline). "
    "All content visible on first paint. Never reference DOM ids that don't exist. "
    "Parents stay opacity:1. Output ONLY complete HTML starting with <!DOCTYPE html>. No fences."
)
USER = "Build a COMPLETE Awwwards-quality portfolio site for 'Atelier Norde' — a Scandinavian industrial design studio. Editorial Fraunces + Inter. Lenis + GSAP + ScrollTrigger + SplitText for reveals. Sections: sticky nav, hero with serif headline, 6 project cards with picsum, 3-col studio philosophy, press strip, contact. Palette: #f6f4ef cream bg, #161614 text, #8b6f47 earth accent. Single file, NO Tailwind."

messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

import time
t0 = time.time()
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=4096, temperature=0.7, top_p=0.9,
                         repetition_penalty=1.05, do_sample=True,
                         pad_token_id=tokenizer.eos_token_id)
t = time.time() - t0
resp = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(f"Generated in {t:.1f}s, {len(resp):,} chars")
print(resp[:1500])
# Save for inspection
with open("/content/stage25_smoke_output.html", "w", encoding="utf-8") as f:
    f.write(resp)
print("Saved to /content/stage25_smoke_output.html")
"""


if __name__ == "__main__":
    # Print the full notebook as sequential cells
    print("=" * 60)
    print("CELL 1 — Install")
    print("=" * 60)
    print(INSTALL_CELL)
    print("\n" + "=" * 60)
    print("CELL 2 — Load base + LoRA")
    print("=" * 60)
    print(LOAD_CELL)
    print("\n" + "=" * 60)
    print("CELL 3 — Dataset")
    print("=" * 60)
    print(DATA_CELL)
    print("\n" + "=" * 60)
    print("CELL 4 — Train")
    print("=" * 60)
    print(TRAIN_CELL)
    print("\n" + "=" * 60)
    print("CELL 5 — Save + push")
    print("=" * 60)
    print(SAVE_CELL)
    print("\n" + "=" * 60)
    print("CELL 6 — Smoke test")
    print("=" * 60)
    print(SMOKE_CELL)
