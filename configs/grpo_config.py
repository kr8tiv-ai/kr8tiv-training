# Cipher Code Kraken - GRPO Configuration
# Target: Reward-based creative code quality reinforcement
# Stage 3 of 4: GRPO uses multi-signal reward functions to reinforce creative code quality
# beyond what preference pairs can teach. The model generates multiple completions per prompt,
# and the reward function scores them based on code structure, creativity, and anti-slop signals.

MODEL_ID = "./cipher-simpo-merged"  # Output from SimPO stage
OUTPUT_DIR = "./cipher-grpo"
MERGED_OUTPUT_DIR = "./cipher-grpo-merged"

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

# GRPO-specific settings
NUM_GENERATIONS = 4          # GRPO group size (generate 4 completions per prompt)
MAX_COMPLETION_LENGTH = 4096

# Training settings
PER_DEVICE_TRAIN_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
NUM_TRAIN_EPOCHS = 1
LEARNING_RATE = 1e-5         # Very low LR for RL stage (100x lower than SFT)
BF16 = True
LOGGING_STEPS = 5
SAVE_STEPS = 50
REPORT_TO = "wandb"
WANDB_PROJECT = "cipher-code-kraken"
WANDB_RUN_NAME = "grpo-stage"

# Dataset
GRPO_DATA_PATH = "data/prompts/grpo_prompts.jsonl"
