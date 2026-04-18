"""Cipher Stage 2.5 v3 — real-data SFT on source-backed creative code.

Paste this into a fresh Colab A100 cell sequence when you want the reproducible
path that matches `Auroraventures/cipher-sft25-real-merged`.

Ground truth dataset:
  - HF dataset: `Auroraventures/cipher-awwwards-sft25` subset `real-scraped-v1`
  - Local JSONL: data/prompts/cipher-real-v1-sft.jsonl

This is the checked-in path for the real-data retrain.
The older `stage25_sft_colab.py` is kept only as a historical record of the
synthetic dataset experiment that collapsed.
"""

# ==========================================================================
# Cell 1 — Install + auth
# ==========================================================================
INSTALL_CELL = r"""
!pip install -q -U "unsloth[cu121-ampere-torch240]==2026.3.2" \
    "transformers==4.47.1" "trl==0.13.0" "peft==0.14.0" \
    "datasets==3.0.0" "accelerate==1.2.1" "bitsandbytes==0.45.0"

from google.colab import userdata
import os, subprocess

for k in ("HF_TOKEN", "HUGGINGFACE_TOKEN", "HF_WRITE_TOKEN"):
    try:
        tok = userdata.get(k)
        if tok:
            os.environ["HF_TOKEN"] = tok
            break
    except Exception:
        continue

print(subprocess.check_output(
    "nvidia-smi --query-gpu=name,memory.total --format=csv", shell=True
).decode())
"""


# ==========================================================================
# Cell 2 — Load base + LoRA
# ==========================================================================
LOAD_CELL = r"""
from unsloth import FastLanguageModel
import torch

MAX_SEQ = 8192
BASE = "Auroraventures/cipher-simpo-merged"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE,
    max_seq_length=MAX_SEQ,
    dtype=None,
    load_in_4bit=True,
    token=os.environ.get("HF_TOKEN"),
)

model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=128,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    use_rslora=True,
    random_state=3407,
)

print("chat_template length:", len(tokenizer.chat_template or ""))
print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
print(f"Free VRAM: {torch.cuda.mem_get_info()[0] / 1e9:.1f} GB")
"""


# ==========================================================================
# Cell 3 — Dataset load + audit
# ==========================================================================
DATA_CELL = r"""
from datasets import load_dataset
from collections import Counter

# Recommended: use the HF dataset subset that backs the real v3 model card.
ds = load_dataset(
    "Auroraventures/cipher-awwwards-sft25",
    "real-scraped-v1",
    split="train",
    token=os.environ.get("HF_TOKEN"),
)

print(f"Loaded {len(ds)} records")
print(ds[0].keys())

source_counts = Counter(ds["source"])
print("Source counts:", dict(source_counts))
assert set(source_counts) == {
    "threejs-official",
    "framer-motion-official",
    "gsap-freefrontend",
}, source_counts
assert sum(source_counts.values()) == len(ds)

def classify_payload(messages):
    assistant = next(m["content"] for m in messages if m["role"] == "assistant")
    low = assistant.lower()
    if "<!doctype" in low or "<html" in low:
        return "html"
    if "import " in assistant or "export " in assistant:
        return "module"
    return "suspicious"

payload_counts = Counter(classify_payload(row["messages"]) for row in ds)
print("Payload kinds:", dict(payload_counts))
assert payload_counts["suspicious"] == 0, payload_counts

def format_example(example):
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}

ds = ds.map(format_example)

sample = ds[0]["text"]
print(sample[:500])
assert "<|turn>user" in sample
assert "<|turn>model" in sample

lens = [len(tokenizer.encode(r["text"])) for r in ds.select(range(min(100, len(ds))))]
print(f"Token lengths — min={min(lens)} mean={sum(lens)//len(lens)} max={max(lens)}")
print(f"Records over MAX_SEQ: {sum(1 for x in lens if x > MAX_SEQ)}")
"""


# ==========================================================================
# Cell 4 — Train
# ==========================================================================
TRAIN_CELL = r"""
from trl import SFTTrainer, SFTConfig
from unsloth.chat_templates import train_on_responses_only

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ,
    args=SFTConfig(
        output_dir="outputs/cipher-sft25-real",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        warmup_ratio=0.03,
        num_train_epochs=2,
        learning_rate=2.0e-5,
        bf16=True,
        logging_steps=5,
        save_strategy="epoch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        report_to="none",
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|turn>user\n",
    response_part="<|turn>model\n<|channel>thought\n<channel|>",
)

print("Starting real-data Stage 2.5 training...")
stats = trainer.train()
print(f"Finished. Final loss: {stats.training_loss:.4f}")
"""


# ==========================================================================
# Cell 5 — Save + push
# ==========================================================================
SAVE_CELL = r"""
MERGED_REPO = "Auroraventures/cipher-sft25-real-merged"

model.save_pretrained("outputs/cipher-sft25-real-lora")
tokenizer.save_pretrained("outputs/cipher-sft25-real-lora")

model.save_pretrained_merged(
    "outputs/cipher-sft25-real-merged",
    tokenizer,
    save_method="merged_16bit",
)

from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])
api.create_repo(MERGED_REPO, repo_type="model", private=False, exist_ok=True)
api.upload_folder(
    folder_path="outputs/cipher-sft25-real-merged",
    repo_id=MERGED_REPO,
    repo_type="model",
    commit_message="Stage 2.5 v3 real-data retrain from cipher-real-v1-sft",
)
print(f"Pushed: https://huggingface.co/{MERGED_REPO}")
"""


# ==========================================================================
# Cell 6 — Smoke test
# ==========================================================================
SMOKE_CELL = r"""
FastLanguageModel.for_inference(model)
import torch, time

SYSTEM = (
    "You are Cipher, the Code Kraken. Build COMPLETE Awwwards-quality single-file HTML. "
    "NO Tailwind. Vanilla CSS only. Only Three.js/GSAP/Lenis (CDN inline). "
    "All content visible on first paint. Never reference DOM ids that don't exist. "
    "Parents stay opacity:1. Output ONLY complete HTML starting with <!DOCTYPE html>. No fences."
)
USER = (
    "Build a COMPLETE Awwwards-quality portfolio for 'Atelier Norde'. "
    "Three.js particle hero, editorial serif typography, Lenis + GSAP ScrollTrigger reveals, "
    "5 semantic sections, dark elegant palette. Single file HTML only."
)

messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

t0 = time.time()
with torch.no_grad():
    out = model.generate(
        **inputs,
        max_new_tokens=4096,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.05,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
resp = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print(f"Generated in {time.time() - t0:.1f}s, {len(resp):,} chars")
print(resp[:1500])
with open("/content/stage25_real_smoke_output.html", "w", encoding="utf-8") as f:
    f.write(resp)
print("Saved to /content/stage25_real_smoke_output.html")
"""


if __name__ == "__main__":
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
