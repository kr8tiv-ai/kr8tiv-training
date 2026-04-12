# Cipher Code Kraken - SimPO Configuration
# Target: Anti-slop preference optimization on SFT-merged model
# Stage 2 of 4: SimPO teaches the model to prefer hand-crafted creative code over generic templates

MODEL_ID = "./cipher-sft-merged"  # Output from SFT stage
OUTPUT_DIR = "./cipher-simpo"
MERGED_OUTPUT_DIR = "./cipher-simpo-merged"

# QLoRA settings (same as SFT)
LOAD_IN_4BIT = True
MAX_SEQ_LENGTH = 4096
DTYPE = None  # auto-detect (bf16 on A100)

# LoRA settings (same as SFT)
LORA_R = 16
LORA_ALPHA = 16
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
USE_GRADIENT_CHECKPOINTING = "unsloth"  # Critical: saves 30% VRAM
RANDOM_STATE = 42

# SimPO-specific settings
LOSS_TYPE = "simpo"
CPO_ALPHA = 0.0          # Pure SimPO (no CPO regularization)
SIMPO_GAMMA = 1.4         # Target reward margin (SimPO paper default)
BETA = 2.0                # SimPO paper recommends 2.0

# Training settings
PER_DEVICE_TRAIN_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
NUM_TRAIN_EPOCHS = 1      # 1 epoch for preference stage
LEARNING_RATE = 5e-5       # Lower LR for preference optimization
BF16 = True
MAX_LENGTH = 4096
MAX_PROMPT_LENGTH = 512
REPORT_TO = "wandb"
WANDB_PROJECT = "cipher-code-kraken"
WANDB_RUN_NAME = "simpo-stage"

# Dataset
SIMPO_DATA_PATH = "data/prompts/simpo_prompts.jsonl"
