# Cipher Code Kraken - SFT Configuration
# Target: Gemma 4 31B QLoRA on A100 40GB
# Stage 1 of 4: Supervised Fine-Tuning on creative code examples

MODEL_ID = "unsloth/gemma-4-31B-it"
OUTPUT_DIR = "./cipher-sft"
MERGED_OUTPUT_DIR = "./cipher-sft-merged"

# QLoRA settings
LOAD_IN_4BIT = True
MAX_SEQ_LENGTH = 4096
DTYPE = None  # auto-detect (bf16 on A100)

# LoRA settings
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
NUM_TRAIN_EPOCHS = 2
LEARNING_RATE = 2e-4
BF16 = True
LOGGING_STEPS = 10
SAVE_STEPS = 100
REPORT_TO = "wandb"
WANDB_PROJECT = "cipher-code-kraken"
WANDB_RUN_NAME = "sft-stage"

# Dataset
SFT_DATA_PATH = "data/prompts/sft_prompts.jsonl"
DATASET_TEXT_FIELD = "text"  # or use formatting_func for conversations
