# Cipher Training Plan — Stages 2.5 → 4 (Awwwards-SOTA)

**Anchored to research:** `DEEP-RESEARCH.md` + `PATTERNS.md` + `library-examples.md`
**Goal:** Close the "good but generic" gap and make Cipher produce Awwwards-caliber single-file HTML reliably.

## The 3 Things That Separate SOTA From The Pack (from research)

1. **Render-in-loop training** — not "does it compile?" but "render to headless Chrome, screenshot, score visually." Every 2025-26 SOTA result (ReLook, VisRefiner, WebGen-Agent, UICoder) hangs on this.
2. **MLLM-as-judge with rubrics** — plain CLIP similarity is too blunt. ArtifactsBench shows structured MLLM rubrics correlate **94.4%** with human preference.
3. **Taste-curated small corpus beats generic 2M-row scrape** — Galileo AI trained on "thousands of real-world interfaces" and got acquired by Google for it. Our 100 SOTD winners are that corpus.

## Cipher's Unique Leverage (why we can win)

| Advantage | Why it matters |
|---|---|
| **Narrow format** (single-file HTML only) | 1/10th v0's surface area. Renders in 500ms on headless Chrome → RL loop is cheap. |
| **Awwwards corpus** (our 100 SOTDs + signatures) | No other player prioritized this. Galileo trained on UI screenshots, v0 trains on generic React. |
| **Motion-first scope** | Dora AI is the only competitor with 3D/animation intent. GSAP+Three.js is open territory. |
| **31B open-weight** | ReLook works at 7B; scaling Forced Optimization to 31B should produce >7B performance at similar training cost. |

---

## Stage 2.5 — SFT on Awwwards-distilled gold (START NOW)

**Why:** Stage 2 (SimPO) removed slop but can't push ceiling above SFT training data. Our SFT data didn't include Awwwards-quality patterns. Fix this before burning GRPO compute.

**Status:** Dataset ready. 288 seed records at `data/prompts/awwwards-stage25-sft.jsonl`.

**Approach:**
1. **Seed 288 deterministic template completions** — already built from gold records (each uses canonical motion stack: Lenis + GSAP + ScrollTrigger + SplitText, palette/fonts extracted from actual winners).
2. **(Optional upgrade)** — teacher reasoning traces from Claude Opus. Each completion prefixed with `<!-- DESIGN RATIONALE: why Lenis here, why this easing, why this palette -->`. Gemma 31B learns *why*, not just *what*.
3. **DMT (Dual-stage Mixed Training)** — mix 90% Awwwards + 10% generic Stage 1 SFT to prevent forgetting.
4. **LoRA training** — r=64, rsLoRA for 31B stability. 2 epochs, lr=5e-5, effective batch 32.
5. **Output:** `Auroraventures/cipher-sft25-merged` + GGUF quant.

**Expected cost:** ~30 minutes on Colab A100. **Ship today.**

**Files ready:**
- `data/awwwards/distilled/awwwards-gold.jsonl` (96 training-ready records)
- `data/prompts/awwwards-stage25-sft.jsonl` (288 SFT pairs, Gemma-4 chat format)
- `companions/cipher/training/stage25_sft_colab.py` (6 Colab cells)

---

## Infrastructure Phase — Render Harness (BETWEEN Stage 2.5 AND Stage 3)

**Gating principle:** Do not start GRPO without this. ReLook's entire edge comes from render validity + visual scoring. Without the harness, we're doing plain DPO and missing 80% of the gain.

**Build:**
- **Playwright headless Chrome** — input HTML string, output (screenshot_t0.png, screenshot_t2s.png, DOM_snapshot.json). <500ms target.
- **MLLM judge** — local Qwen2.5-VL-72B via vLLM *or* Claude Sonnet API (cheaper, faster to ship). Fixed rubric: 5-point scores on { typography_craft, motion_quality, visual_hierarchy, whitespace, concept_coherence }.
- **Rubric judge (code-side)** — LLM-as-judge on code: { uses_lenis, uses_gsap, uses_scrolltrigger, has_splittext, oklch_colors, clamp_type_scale, sections≥3, no_tailwind, no_broken_refs, has_motion_init }.
- **Motion execution test** — Playwright: inject code, scroll 500px, check scroll position changed; hover hero, check opacity animated. DOM-mutation delta ≠ 0 ⟹ pass.
- **Cache layer** — SHA256(HTML) → screenshots/scores. Avoid re-rendering identical outputs during rollout.

**Time cost:** ~2 days of focused engineering. Critical path.

---

## Stage 3 — GRPO reproducing ReLook at 31B

**Reward composition (from ReLook paper, adapted):**
```
R_total = R_render_valid
        × (0.40 × R_MLLM_visual
         + 0.25 × R_rubric_code
         + 0.15 × R_motion_exec
         + 0.10 × R_concept  (kraken voice, originality — LLM-as-judge)
         + 0.10 × R_craft    (CSS quality, semantic HTML))
        × R_length_penalty
```

- **Zero-reward gate:** `R_render_valid = 0` if Playwright throws or page is blank. Prevents reward hacking.
- **Forced Optimization (ReLook's trick):** for each rollout, resample up to 10× until score strictly improves over previous round. Unblocks learning signal on hard prompts.
- **Group size 8, batch 64 prompts, 40 steps.** Same budget as ReLook 7B; A100 40GB should handle 31B with LoRA on top of cipher-sft25.

**Prompt corpus:** 500-1000 prompts derived from SOTD theme clusters (portfolio, agency, SaaS, product launch, 3D experience, editorial). Each prompt paired with 2-3 retrieved gold exemplars in-context.

**Output:** `Auroraventures/cipher-grpo-merged` + GGUF.

**Expected cost:** ~8 hours A100 + MLLM judge inference.

---

## Stage 4 — KTO on human + synthetic preferences

**Why KTO over DPO:** ArtifactsBench-style scoring produces binary good/bad labels, not paired preferences. KTO handles unpaired binary signals natively.

**Data sources:**
- **Human-labeled** — Matt labels 200-500 outputs in a weekend (thumbs up/down on own test prompts).
- **Synthetic A vs baseline** — Cipher-SFT25 vs Claude Sonnet baseline on same prompts. MLLM judge picks winner → binary label.
- **Checkpoint-vs-checkpoint** — Cipher-GRPO-step20 vs step40. Assumes later checkpoints tend to be better; validates the assumption.
- **Anti-slop mining** — take Stage 2 SimPO rejection patterns (purple gradients, Bootstrap fallbacks, emoji-heavy, generic "modern minimal"), generate targeted anti-slop pairs.

**Expected cost:** ~4 hours A100. Budget: ~$10.

---

## Evaluation — ArtifactsBench methodology, always-on

Fixed 50-prompt Awwwards-prompt test set. For every checkpoint run:
- Render harness (from Infra Phase)
- MLLM visual score (mean across 5 rubric dimensions)
- Code-rubric pass-rate
- Motion-exec pass-rate
- Comparison vs baselines: Claude Sonnet, GPT-5, v0 (via API), Cipher-SFT1, Cipher-SimPO, Cipher-SFT25, etc.

Publish to a public leaderboard in kr8tiv-training/evals/leaderboard.md. See the gap close.

---

## Competitive Moat Plan (composite pipeline at inference)

Even with a great model, wrap Cipher in a v0-style composite:

1. **Retrieval** — embed user prompt, pull top-3 SOTD exemplars from `awwwards-gold.jsonl`.
2. **Cipher generation** — single pass with retrieved context in system prompt.
3. **Self-critique round** — ReLook-style: render → MLLM judge → rewrite if score < threshold, up to 2 rounds.
4. **Autofix pass** — deterministic AST fixes (Lenis init, GSAP.registerPlugin, viewport meta, missing closing tags, broken DOM refs).

This composite + Cipher + the corpus is the moat. **Nobody else has all three for Awwwards.**

---

## Timeline

| Week | Work | Output |
|---|---|---|
| **NOW** | Stage 2.5 SFT on Colab A100 | `cipher-sft25-merged` + GGUF |
| +2 days | Render harness (Playwright + MLLM judge + rubric) | `scripts/render_harness/` |
| +1 week | Stage 3 GRPO with ReLook-style reward | `cipher-grpo-merged` + GGUF |
| +1 week | Stage 4 KTO on pref data | `cipher-kto-merged` + GGUF |
| Ongoing | ArtifactsBench-style eval every commit | `evals/leaderboard.md` |

---

## The Action Item For Right Now

Fire Stage 2.5 training. Everything else is already planned. Cipher-SFT25 should land in ~45 min including Colab spin-up + GGUF conversion.
