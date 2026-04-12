# Cipher Code Kraken - KTO Configuration
# Target: Binary feedback alignment (final training stage)
# Stage 4 of 4: KTO uses binary thumbs-up/down signals to do final alignment.
# This is the lightest training stage -- refines the model based on simple yes/no feedback.

MODEL_ID = "./cipher-grpo-merged"  # Output from GRPO stage
OUTPUT_DIR = "./cipher-kto"
MERGED_OUTPUT_DIR = "./cipher-final-merged"

# QLoRA settings (consistent across all stages)
LOAD_IN_4BIT = True
MAX_SEQ_LENGTH = 4096
DTYPE = None  # auto-detect (bf16 on A100)

# LoRA settings (consistent across all stages)
LORA_R = 16
LORA_ALPHA = 16
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
USE_GRADIENT_CHECKPOINTING = "unsloth"  # Critical: saves 30% VRAM
RANDOM_STATE = 42

# Training settings
PER_DEVICE_TRAIN_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
NUM_TRAIN_EPOCHS = 1
LEARNING_RATE = 5e-6       # Very low LR for final alignment (200x lower than SFT)
BF16 = True
MAX_LENGTH = 4096
MAX_PROMPT_LENGTH = 512
REPORT_TO = "wandb"
WANDB_PROJECT = "cipher-code-kraken"
WANDB_RUN_NAME = "kto-stage"

# Dataset
KTO_DATA_PATH = "data/prompts/kto_prompts.jsonl"
