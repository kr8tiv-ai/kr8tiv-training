# ============================================================================
# SFT Configuration — Best-in-Class for Gemma 4 31B on A100 40GB
# Updated: 2026-04-12 | Sources: Unsloth docs, rsLoRA paper, LoRA guide
# ============================================================================

MODEL_ID = "unsloth/gemma-4-31B-it"
LOAD_IN_4BIT = True
DTYPE = None

# LoRA — r=64 with rsLoRA (r=16 is too low for 31B, confirmed by research)
LORA_R = 64
LORA_ALPHA = 64                # 1:1 ratio with rsLoRA
USE_RSLORA = True              # CRITICAL: unlocks full r=64 capacity
LORA_DROPOUT = 0.0
BIAS = "none"
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
USE_GRADIENT_CHECKPOINTING = "unsloth"  # String, not boolean

LEARNING_RATE = 2e-4
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.03
WEIGHT_DECAY = 0.01
MAX_GRAD_NORM = 1.0
EPOCHS = 2
PER_DEVICE_BATCH_SIZE = 1      # A100 40GB with 31B QLoRA
GRADIENT_ACCUMULATION = 4      # Effective batch = 4
MAX_SEQ_LENGTH = 8192          # 8K achievable on A100 with Unsloth
BF16 = True                    # MUST be bf16, NEVER fp16
OPTIM = "adamw_8bit"
SEED = 42
PACKING = True
DATASET_TEXT_FIELD = "text"

OUTPUT_DIR = "./cipher-sft"
MERGED_OUTPUT_DIR = "./cipher-sft-merged"
SAVE_STEPS = 200
SAVE_TOTAL_LIMIT = 2
LOGGING_STEPS = 10
REPORT_TO = "none"
RANDOM_STATE = 42
NUM_TRAIN_EPOCHS = 2
PER_DEVICE_TRAIN_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
BF16 = True
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"]
WANDB_PROJECT = "cipher-code-kraken"
WANDB_RUN_NAME = "sft-stage"
SFT_DATA_PATH = "./data/prompts/awwwards-sft.jsonl"

DATA_MIX = {
    "frontend_tutorials": 0.30,
    "persona_conversations": 0.25,
    "tool_use_trajectories": 0.15,
    "design_critiques": 0.15,
    "accessibility_training": 0.10,
    "safety_alignment": 0.05,
}
QUALITY_THRESHOLD = 0.75
