# ============================================================================
# SimPO Configuration — Best-in-Class for Gemma 4 31B on A100 40GB
# Updated: 2026-04-12 | Sources: SimPO paper NeurIPS 2024 (Table 5)
# ============================================================================

MODEL_ID = "./cipher-sft-merged"
LOAD_IN_4BIT = True

LORA_R = 64
LORA_ALPHA = 64
USE_RSLORA = True
LORA_DROPOUT = 0.0
BIAS = "none"
USE_GRADIENT_CHECKPOINTING = "unsloth"

# SimPO — Paper-optimal values
LOSS_TYPE = "simpo"
CPO_ALPHA = 0.0                # Pure SimPO (no BC regularization)
BETA = 10.0                    # SimPO paper Table 5 optimal (NOT DPO scale)
SIMPO_GAMMA = 2.5              # Reward margin. Ratio gamma/beta = 0.25 (paper optimal)

LEARNING_RATE = 5e-7           # Tuned: 3e-7 to 1e-6 range
LR_SCHEDULER = "cosine"
WARMUP_RATIO = 0.1             # 10% warmup for preference stages
WEIGHT_DECAY = 0.0
EPOCHS = 1
PER_DEVICE_BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 128    # CRITICAL: Paper recommends effective batch 128
MAX_SEQ_LENGTH = 4096
BF16 = True
OPTIM = "adamw_8bit"
SEED = 42

# Tuning order: 1) LR → 2) gamma/beta ratio → 3) absolute beta
# If loss noisy: increase grad_accum to 256
# If chosen/rejected rewards converge: increase gamma to 3.0-5.0

OUTPUT_DIR = "./cipher-simpo"
SAVE_STEPS = 100
LOGGING_STEPS = 10
REPORT_TO = "none"
