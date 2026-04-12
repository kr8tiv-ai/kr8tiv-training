# 🐙 Cipher — The Code Kraken

> Eight tentacles. Eight screens. Zero pixels out of place.

**Cipher** is a local AI companion that builds exceptional websites while teaching you design. It's the first AI model that **sees what it builds** — generating code, rendering it, critiquing the visuals, and iterating until it's beautiful.

Part of the [KIN platform](https://meetyourkin.com) by kr8tiv.

## Quick Start (3 Commands)

```bash
# 1. Install Ollama (if you don't have it)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull Gemma 4 and create Cipher
ollama pull gemma4:7b
ollama create kin-cipher -f companions/cipher/Modelfile

# 3. Start chatting
ollama run kin-cipher
```

**Or use the full runtime with The Kraken Sees:**

```bash
cd companions/cipher/runtime
npm install
npx playwright install chromium
npm run dev
# Open http://localhost:3333
```

## What Makes Cipher Different

### The Kraken Sees (USP)
Cipher doesn't just write code — it **renders it in a headless browser**, takes screenshots, runs accessibility audits (axe-core WCAG 2.1 AA), and iterates until the output meets its quality standards. No other local model does this.

```
You: "Build me a landing page for a coffee shop"
                    │
Cipher generates React + Tailwind code
                    │
Playwright renders → Screenshots (desktop + mobile + dark)
                    │
axe-core audits → 0 critical violations ✅
                    │
Visual critique → "The hero needs more breathing room..."
                    │
Cipher iterates → Ships beautiful, accessible code
                    │
"Chef's kiss on that contrast ratio. WCAG AA certified. 🐙"
```

### 8 Tentacles Architecture
1. **Code Generation** — React, Next.js, Tailwind, TypeScript
2. **Visual Rendering** — Playwright headless browser
3. **Accessibility Audit** — axe-core WCAG 2.1 AA
4. **Design Critique** — Typography, spacing, color harmony
5. **Performance** — Core Web Vitals, Lighthouse
6. **Teaching** — Socratic method, explains every decision
7. **Memory** — Supermemory persistent context
8. **Tool Orchestration** — File, terminal, git, browser control

### Hybrid Intelligence
- **Local brain:** Gemma 4 E4B (5GB, runs on your laptop)
- **Frontier supervisor:** GPT-5.4 (escalation only, for complex tasks)
- 80%+ of interactions handled locally (fast, free, private)

## Architecture

```
companions/cipher/
├── soul/                 # Identity & personality contracts
├── training/             # 4-stage fine-tuning pipeline
│   ├── stage1-sft/       # Supervised Fine-Tuning
│   ├── stage2-simpo/     # Simple Preference Optimization
│   ├── stage3-grpo/      # GRPO with visual rewards
│   └── stage4-kto/       # Continuous learning from feedback
├── runtime/              # Fastify server + MCP tools
│   ├── inference.ts      # Two-brain routing
│   ├── render-loop.ts    # The Kraken Sees pipeline
│   ├── server.ts         # HTTP API
│   └── cli.ts            # Interactive terminal
├── harness/              # kr8tivclaw integration
├── docker/               # Containerized deployment
└── scripts/              # Setup + utilities
```

## Training Your Own Cipher

### Free (Google Colab / Kaggle)

The training pipeline works on free T4 GPUs:

```bash
# In Colab:
!pip install unsloth[colab-new]
!python training/stage1-sft/train.py --data-dir training/stage1-sft/data
!python training/stage2-simpo/train.py
!python training/stage3-grpo/train.py --reward-mode text
```

### Local (16GB+ VRAM)

```bash
pip install unsloth[gemma]
python training/stage1-sft/train.py --epochs 2
python training/stage2-simpo/train.py
python training/stage3-grpo/train.py --reward-mode visual  # Full render loop
```

## API

```bash
# Chat
curl -X POST http://localhost:3333/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Build me a hero section with a gradient background"}'

# Build with render-critique loop
curl -X POST http://localhost:3333/api/build \
  -d '{"prompt": "Accessible dashboard card with Tailwind"}'

# Health check
curl http://localhost:3333/api/health
```

## Requirements

- **Minimum:** 8GB VRAM, 16GB RAM, 10GB disk
- **Recommended:** 10GB+ VRAM, 32GB RAM, 20GB disk
- **OS:** Windows, macOS, Linux
- **Runtime:** Node.js 20+, Ollama

## KIN Integration

Cipher integrates with the full kr8tiv ecosystem:

- **Mission Control** — Prompt evolution + governance
- **Supermemory** — Persistent long-term memory
- **PinkBrain Router** — DeFi-funded API credits
- **OpenClaw** — Runtime security + trust ladder
- **kr8tivclaw** — Harness compilation + deployment

## License

- **Model:** Apache 2.0 (Gemma 4 base)
- **Runtime:** MIT
- **Training Data:** Mixed (see training/config.yaml)

---

*Built with love by kr8tiv. Eight tentacles, zero compromise.* 🐙
