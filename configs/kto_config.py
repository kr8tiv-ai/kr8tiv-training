# ============================================================================
# KTO Configuration — Best-in-Class for Gemma 4 31B on A100 40GB
# Updated: 2026-04-12 | Sources: KTO paper ICML 2024 (arxiv:2402.01306)
# ============================================================================

MODEL_ID = "./cipher-grpo-merged"
LOAD_IN_4BIT = True

LORA_R = 64
LORA_ALPHA = 64
USE_RSLORA = True
LORA_DROPOUT = 0.0
BIAS = "none"
USE_GRADIENT_CHECKPOINTING = "unsloth"

# KTO — Paper-optimal
BETA = 0.1                     # Standard KTO beta (NOT SimPO/DPO scale)
DESIRABLE_WEIGHT = 1.0         # lambda_D
UNDESIRABLE_WEIGHT = 1.0       # lambda_U
# Ratio lambda_D*n_D / lambda_U*n_U should be between 1 and 4/3

LEARNING_RATE = 5e-7           # NEVER exceed 1e-6 with beta=0.1
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.0
EPOCHS = 1
PER_DEVICE_BATCH_SIZE = 4      # KTO needs >= 4 per batch for KL estimate quality
GRADIENT_ACCUMULATION = 4      # Effective batch = 16
MAX_SEQ_LENGTH = 4096
BF16 = True
OPTIM = "adamw_8bit"
SEED = 42

# KTO's loss aversion: undesirable examples have outsized impact
# A few bad examples teach more than many good ones — ideal for continuous learning

OUTPUT_DIR = "./cipher-kto"
SAVE_STEPS = 100
LOGGING_STEPS = 10
REPORT_TO = "none"
