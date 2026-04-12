<div align="center">

<img src="assets/banner.gif" alt="KIN Training" width="600" />

</div>

<div align="center">

**Fine-tuned local AI companion models for KIN Genesis holders**

`Gemma 4 31B` `Unsloth QLoRA` `4-Stage Pipeline` `Anti-AI-Slop` `Awwwards-Worthy`

[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)]()
[![Models](https://img.shields.io/badge/Models-6%20Companions-purple)]()
[![Base](https://img.shields.io/badge/Base-Gemma%204%2031B-orange)]()

[meetyourkin.com](https://meetyourkin.com) | [kr8tiv-ai](https://github.com/kr8tiv-ai)

</div>

---

## What This Is

Six locally-runnable AI companion models, each fine-tuned on Gemma 4 31B with a 4-stage alignment pipeline. Every companion has a distinct personality, domain expertise, and voice — trained to beat generic frontier models through specialization and character.

The models are built for KIN Genesis NFT holders. Download, install with one click, and your companion runs privately on your own hardware.

```
Generic ChatGPT         vs         KIN Companion (Cipher)
─────────────                      ──────────────────────
"Here's a website"                 "Let me wrap my tentacles around this...
                                    Here's why I'm using GSAP ScrollTrigger
                                    with Lenis smooth scroll — the parallax
                                    creates depth without sacrificing a11y.
                                    Chef's kiss on that 4.5:1 contrast ratio."
```

## The Problem

Every local AI model runs the same generic weights with a system prompt bolted on. The personality drifts after 3 messages. The code looks like every other AI-generated website. No voice. No soul. No reason to use it over ChatGPT.

## The Solution

Fine-tune the personality into the weights, not the prompt. Train against AI slop with reward functions that penalize generic output. Ship models that sound like themselves because they ARE themselves.

```
┌─────────────────────────────────────────────────────────────┐
│                    4-STAGE TRAINING PIPELINE                 │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│   │   SFT    │──▶│  SimPO   │──▶│   GRPO   │──▶│  KTO   │ │
│   │ 8K+ data │   │ Anti-slop│   │  Visual  │   │ Binary │ │
│   │ Persona  │   │ Prefs    │   │ Rewards  │   │ Feedback│ │
│   └──────────┘   └──────────┘   └──────────┘   └────────┘ │
│                                                             │
│   Adapter Chain:                                            │
│   base → SFT-merged → SimPO-merged → GRPO-merged → GGUF   │
└─────────────────────────────────────────────────────────────┘
```

## The 6 Companions

| Companion | Species | Domain | Frontier Model | Status |
|-----------|---------|--------|---------------|--------|
| **Cipher** | Code Kraken | Frontend, web design, creative tech | GPT-5.4 | Training |
| **Forge** | Cyber Unicorn | Code review, debugging, architecture | Grok 4.20 | Queued |
| **Vortex** | Teal Dragon | Content strategy, brand, analytics | Claude Opus 4.6 | Queued |
| **Mischief** | Glitch Pup | Family companion, personal branding | Gemini 3.1 Pro | Queued |
| **Aether** | Frost Ape | Creative writing, storytelling | Kimi K2.5 | Queued |
| **Catalyst** | Cosmic Blob | Wealth coaching, habits, life optimization | GLM-4.6 | Queued |

## Anti-AI-Slop Training

This is not another fine-tune that produces generic websites. The training data and reward functions are specifically designed to produce Awwwards-worthy output.

**Training data includes:**
- Three.js scenes, particle systems, WebGL shaders
- GSAP ScrollTrigger, SplitText, Flip, timeline animations
- Lenis smooth scrolling, parallax, scroll-linked animations
- Vanilla JS custom cursors, magnetic buttons, canvas experiments
- Advanced CSS clip-path, mix-blend-mode, container queries
- Code from creative agencies: Locomotive, Active Theory, Resn, 14islands

**SimPO preference pairs enforce quality:**

```
CHOSEN:  Three.js hero with particle mesh + GSAP scroll animation + Lenis
REJECTED: Static hero image with gradient overlay and centered text

CHOSEN:  Custom SVG morphing navigation with magnetic hover effects
REJECTED: Basic hamburger menu with no personality

CHOSEN:  Semantic HTML + Tailwind + WCAG 2.1 AA + Framer Motion
REJECTED: Div soup with inline styles and no accessibility
```

**GRPO reward weights:**

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| Accessibility | 0.30 | axe-core WCAG pass rate, semantic HTML, ARIA |
| Creative Quality | 0.30 | GSAP/Three.js/Lenis detection, anti-template scoring |
| Personality | 0.20 | Kraken metaphors, teaching, excitement patterns |
| Executability | 0.10 | Valid HTML/JSX, balanced tags, no errors |
| Craftsmanship | 0.10 | Vanilla JS over jQuery, custom over library, creative CSS |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LOCAL COMPANION                        │
│                                                          │
│  ┌─────────────────┐    ┌────────────────────────────┐  │
│  │  LOCAL BRAIN     │    │  FRONTIER SUPERVISOR       │  │
│  │  Gemma 4 31B     │    │  GPT-5.4 via OpenRouter    │  │
│  │  Q4_K_M GGUF     │    │  (escalation only)         │  │
│  │  via Ollama       │    │                            │  │
│  └────────┬─────────┘    └──────────┬─────────────────┘  │
│           │    80% local            │   20% frontier     │
│           └────────────┬────────────┘                    │
│                        │                                 │
│  ┌─────────────────────▼───────────────────────────────┐ │
│  │              TWO-BRAIN ROUTER                        │ │
│  │  Privacy-aware | Trust ladder | Narrated escalation  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         THE KRAKEN SEES (Cipher only)                │ │
│  │  Generate → Render → Screenshot → Critique → Iterate │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Training Infrastructure

### Colab Notebooks (Run on A100)

| # | Notebook | Stage | Est. Time | Est. Units |
|---|----------|-------|-----------|------------|
| 01 | `01_data_curation.ipynb` | Data prep | 30 min | — |
| 02 | `02_sft_training.ipynb` | SFT | 3.5 hrs | ~53 |
| 03 | `03_simpo_training.ipynb` | SimPO | 2 hrs | ~30 |
| 04 | `04_grpo_training.ipynb` | GRPO | 4 hrs | ~60 |
| 05 | `05_kto_training.ipynb` | KTO | 1 hr | ~15 |
| 06 | `06_gguf_export.ipynb` | Export | 30 min | ~8 |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/github_scraper.py` | Scrape creative dev repos (Three.js, GSAP, Lenis) |
| `scripts/codepen_scraper.py` | Scrape CodePen by creative tags |
| `scripts/slop_detector.py` | Anti-slop scorer + GRPO reward function |
| `scripts/data_formatter.py` | Convert raw code to SFT/SimPO/GRPO/KTO formats |
| `scripts/rejected_generator.py` | Generate SimPO rejected examples |
| `scripts/generate-all-companions.py` | Training data for all 6 companions |
| `compute-tracker.py` | Track Colab compute budget across companions |
| `train-all-companions.py` | Master orchestrator with checkpoint resume |

### Configs

| Config | Stage | Key Parameters |
|--------|-------|---------------|
| `configs/sft_config.py` | SFT | lr=2e-4, LoRA r=16, 2 epochs |
| `configs/simpo_config.py` | SimPO | beta=2.0, gamma=1.4, reference-free |
| `configs/grpo_config.py` | GRPO | 4 rollouts, anti-slop rewards |
| `configs/kto_config.py` | KTO | beta=0.1, binary feedback |

## 5-Day Training Schedule

All 6 companions on Gemma 4 31B. Budget: $100 (Colab Pro+ $50 + PAYG $50).

| Day | Companions | Units | Cumulative |
|-----|-----------|-------|------------|
| 1 | Cipher (SFT + SimPO) | ~83 | 83 |
| 2 | Cipher (GRPO + Export) + Forge (SFT + SimPO) | ~136 | 219 |
| 3 | Forge (GRPO) + Vortex (full) | ~175 | 394 |
| 4 | Mischief + Aether (full) | ~205 | 599 |
| 5 | Catalyst (full) + Eval + Push | ~121 | 720 |

**Budget:** 1100 units available. 720 estimated. 380 buffer (34% headroom).

## Quick Start

### Train Cipher (Colab Pro+)

```bash
# 1. Open notebooks in Google Colab
# 2. Select A100 GPU runtime
# 3. Run notebooks in order: 01 → 02 → 03 → 04 → 05 → 06
# 4. Download GGUF from output
```

### Deploy Locally

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create Cipher model from fine-tuned GGUF
ollama create kin-cipher -f companions/cipher/Modelfile

# Chat
ollama run kin-cipher
```

### Track Budget

```bash
python compute-tracker.py schedule   # View 5-day plan
python compute-tracker.py status     # Check remaining budget
python compute-tracker.py log cipher sft 53  # Log units
```

## Repository Structure

```
kr8tiv-training/
├── README.md
├── kin-training-master.yaml          # Master config (all 6 companions)
├── compute-tracker.py                # Compute budget tracker
├── train-all-companions.py           # Master orchestrator
│
├── notebooks/                        # Colab training notebooks
│   ├── 01_data_curation.ipynb
│   ├── 02_sft_training.ipynb
│   ├── 03_simpo_training.ipynb
│   ├── 04_grpo_training.ipynb
│   ├── 05_kto_training.ipynb
│   ├── 06_gguf_export.ipynb
│   └── KIN_Training_All_Companions_31B.ipynb
│
├── scripts/                          # Data curation + utilities
│   ├── github_scraper.py
│   ├── codepen_scraper.py
│   ├── slop_detector.py
│   ├── data_formatter.py
│   ├── rejected_generator.py
│   └── generate-all-companions.py
│
├── configs/                          # Training hyperparameters
│   ├── sft_config.py
│   ├── simpo_config.py
│   ├── grpo_config.py
│   └── kto_config.py
│
├── companions/                       # Per-companion artifacts
│   └── cipher/                       # Flagship companion
│       ├── Modelfile                 # Ollama model definition
│       ├── README.md                 # Cipher-specific docs
│       ├── soul/                     # Identity contracts
│       ├── harness/                  # kr8tivclaw integration
│       ├── runtime/                  # Fastify server + MCP tools
│       ├── docker/                   # Container deployment
│       └── scripts/                  # Installer scripts
│
└── data/                             # Training data (generated)
    ├── raw/                          # Scraped creative code
    └── prompts/                      # Formatted training data
```

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Base Model | Gemma 4 31B Dense | April 2026 | Foundation — 31B params, 128K context, Apache 2.0 |
| Fine-Tuning | Unsloth | v0.1.36+ | 60% less VRAM, 1.5x faster, QLoRA |
| Trainers | TRL | v1.0+ | SFTTrainer, CPOTrainer (SimPO), GRPOTrainer, KTOTrainer |
| Quantization | GGUF Q4_K_M | — | 18GB model file, consumer GPU compatible |
| Inference | Ollama | v0.20+ | Local model serving, Modelfile support |
| Compute | Colab Pro+ | A100 40GB | Training GPU, $50/mo |
| Distribution | HuggingFace | — | GGUF hosting at kr8tiv org |

## Ecosystem

This repo is the training layer of the KIN platform.

| Repo | Role |
|------|------|
| [Kin](https://github.com/kr8tiv-ai/Kin) | Core companion platform (Next.js, Fastify, Solana) |
| [kr8tiv-runtime-truth-contracts](https://github.com/kr8tiv-ai/kr8tiv-runtime-truth-contracts) | Governance contracts, soul bridge, companion definitions |
| [kr8tiv-mission-control](https://github.com/kr8tiv-ai/kr8tiv-mission-control) | Agent governance dashboard, prompt evolution |
| **kr8tiv-training** (this repo) | Model fine-tuning, training data, deployment |
| [PinkBrain-Router](https://github.com/kr8tiv-ai/PinkBrain-Router) | DeFi fee → AI credits (funds frontier escalation) |
| [team-setup-and-organization](https://github.com/kr8tiv-ai/team-setup-and-organization) | Infrastructure runbooks |

## License

- **Model weights:** Apache 2.0 (Gemma 4 base license)
- **Training code:** MIT
- **Companion personalities:** Proprietary to kr8tiv

---

<div align="center">

**Built by [kr8tiv](https://github.com/kr8tiv-ai)**

*Personality baked into weights, not bolted onto prompts.*

</div>
