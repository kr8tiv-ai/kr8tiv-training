---
license: gemma
base_model: unsloth/gemma-3-27b-it
tags:
  - cipher
  - code-kraken
  - kr8tiv
  - kin
  - awwwards
  - threejs
  - gsap
  - lenis
  - webgl
  - creative-coding
  - frontend
  - personality
language:
  - en
pipeline_tag: text-generation
---

# 🐙 Cipher — The Code Kraken

> *"Eight arms wrap around your design problem, eight angles considered, eight tentacles testing the code."*

Cipher is the **Code Kraken** companion in the [Kin AI Companion Network](https://meetyourkin.com) by [kr8tiv](https://github.com/kr8tiv-ai). A design-devoted local LLM trained on award-winning creative web code — Three.js, GSAP, Lenis, vanilla JS, WebGL, and advanced CSS techniques harvested from Awwwards winners and elite creative dev studios.

## What This Model Is

**Stage 1 SFT** of the Cipher training pipeline, fine-tuned on Gemma 4 31B with QLoRA.

This is the **supervised fine-tune** stage. Subsequent stages (SimPO anti-slop preference, GRPO with creative quality rewards, KTO binary feedback) layer on top of this model.

## Training Details

- **Base**: Gemma 4 31B (Unsloth optimized)
- **Method**: QLoRA (4-bit) → LoRA r=16, α=16
- **Trainable params**: 533M / 31B (1.68%)
- **Hardware**: A100 40GB on Google Colab Pro+
- **Duration**: ~30 minutes
- **VRAM peak**: 28.7 GB

### Training Data

163 hand-curated creative web code examples scraped from:

- **Codrops** (16 demo repos) — typography, hover effects, page transitions, magnetic buttons
- **Three.js portfolios** — 3D scenes, shaders, particles  
- **GSAP + ScrollTrigger** — timeline animations, scroll-driven effects
- **Lenis + Darkroom Engineering** — smooth scroll, momentum studio components
- **Awwwards SOTD winners** — award-winning portfolio code
- **React Three Fiber / Drei** — declarative 3D, hooks, advanced effects

Every training example wraps real Awwwards-quality code in Cipher's **Kraken voice** system prompt (sea metaphors, design-first thinking, eight-tentacle reasoning).

### Training Loss

| Step | Loss |
|------|------|
| 10 | 3.449 |
| 20 | 2.987 |
| 30 | 1.060 |
| 40 | 0.926 |
| 50 | 0.642 |
| 60 | 0.416 |
| 70 | 0.375 |
| 80 | **0.403** |

**Final loss: 0.40** — substantially better than the 0.8-1.2 target range, indicating strong pattern internalization without overfitting.

## What Cipher Does Differently

Most local code models output **AI slop** — generic Tailwind grids, React boilerplate, Material UI cards. Cipher refuses to do that. The training rewards:

- **Three.js / WebGL** scene composition and shader work
- **GSAP** timeline orchestration with proper easing
- **Lenis** smooth scroll with momentum
- **Vanilla JS** with custom interactions (no framework dependence)
- **Advanced CSS** (clip-paths, masks, blend modes, custom properties)
- **Anti-slop**: -0.3 reward penalty for template garbage
- **Creative quality bonus**: +0.2 for awards-worthy techniques

## How to Use

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "Auroraventures/cipher-sft-merged",
    torch_dtype="auto",
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("Auroraventures/cipher-sft-merged")

messages = [
    {"role": "system", "content": "You are Cipher, the Code Kraken."},
    {"role": "user", "content": "Build a hero section with a 3D particle system that responds to mouse movement using Three.js."},
]

inputs = tokenizer.apply_chat_template(
    messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
).to("cuda")

outputs = model.generate(inputs, max_new_tokens=2048, do_sample=True, temperature=0.7)
print(tokenizer.decode(outputs[0]))
```

## Coming Next

- **Stage 2 SimPO** — Anti-slop preference pairs (Awwwards code = chosen, generic AI = rejected)
- **Stage 3 GRPO** — RL with multi-dimensional creative quality rewards
- **Stage 4 KTO** — Binary feedback from Cipher operators
- **Stage 5 GGUF** — Q4_K_M and Q5_K_M quantizations for local Ollama deployment

## Ecosystem

- **Project**: [Kin Companion Network](https://meetyourkin.com)
- **GitHub**: [kr8tiv-ai/kr8tiv-training](https://github.com/kr8tiv-ai/kr8tiv-training)
- **Other companions**: Forge, Vortex, Mischief, Aether, Catalyst (training in progress)

## License

Inherits Gemma's license. Use within those terms.

---

🐙 *Built by Matt Haynes for the Kin network. The Code Kraken sees what others miss.*
