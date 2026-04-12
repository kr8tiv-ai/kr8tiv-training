# ============================================================================
# GRPO Configuration — Best-in-Class for Gemma 4 31B on A100 40GB
# Updated: 2026-04-12 | Sources: DeepSeekMath, TRL GRPOTrainer docs
# ============================================================================

MODEL_ID = "./cipher-simpo-merged"
LOAD_IN_4BIT = True

LORA_R = 64
LORA_ALPHA = 64
USE_RSLORA = True
LORA_DROPOUT = 0.0
BIAS = "none"
USE_GRADIENT_CHECKPOINTING = "unsloth"

# GRPO — Research-optimal
NUM_GENERATIONS = 4            # 4 rollouts per prompt (best quality on A100 40GB)
MAX_PROMPT_LENGTH = 2048
MAX_COMPLETION_LENGTH = 4096
EPSILON = 0.2                  # PPO-style clip
BETA = 0.0                     # NO KL penalty — not essential, saves memory

LEARNING_RATE = 5e-6
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.03
WEIGHT_DECAY = 0.0
EPOCHS = 1
PER_DEVICE_BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4      # Effective: 4 prompts x 4 generations = 16 rollouts
MAX_SEQ_LENGTH = 4096
BF16 = True
OPTIM = "adamw_8bit"
SEED = 42

# Cipher reward weights (accessibility-first + anti-slop)
REWARD_WEIGHTS = {
    "accessibility": 0.30,
    "creative_quality": 0.30,
    "personality": 0.20,
    "executability": 0.10,
    "craftsmanship": 0.10,
}
SLOP_PENALTY = -0.3
CREATIVE_BONUS = 0.2
IMPORT_VALIDATION = True
REPETITION_THRESHOLD = 0.5
CODE_BLOCK_REQUIRED = True

OUTPUT_DIR = "./cipher-grpo"
SAVE_STEPS = 50
LOGGING_STEPS = 5
REPORT_TO = "none"
