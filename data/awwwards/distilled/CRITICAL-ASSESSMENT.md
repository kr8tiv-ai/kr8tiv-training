# Critical Assessment: Is Our Approach Right?

*Research date: 2026-04-15. Compiled from v0/Vercel engineering posts, ReLook/VisRefiner/Design2Code papers, leaked system prompts (x1xhlol repo, Simon Willison's writeup), Hugging Face fine-tuning literature, and current academic work on synthetic data and model collapse.*

---

## TL;DR (5 bullets, brutally honest)

1. **No serious commercial creative-web AI is fine-tuning a 31B base model. None.** v0 explicitly rejected fine-tuning open models because "proprietary models outperform open models on tasks relevant to v0 by a wide margin, especially code generation with multimodal input." Lovable, Bolt, Cursor, Magic Patterns — they are all Claude Sonnet/GPT with system prompts, curated RAG, and narrow autofixer models. The "fine-tune a local model to beat Claude on creative output" premise is the part of the approach that is structurally wrong.
2. **Academic vision-RL (ReLook, VisRefiner) runs on 7B/8B, gets +2 to +6 points on Design2Code, and measures *fidelity to a target screenshot*, not creative quality.** None of this literature claims to produce Awwwards-caliber work. They are solving "render matches reference" — a different problem from "produce original award-winning design from a brief."
3. **54 synthetic records written by an AI is textbook model collapse territory.** Recursive training on self-generated data compresses the output distribution. Epoch AI and multiple 2025 reviews are explicit: synthetic data is an expansion layer on top of curated human data, not a replacement. 288 failed by memorizing (loss 0.017). 54 is producing "clean but generic" because the model has nothing left to learn that isn't already in the Gemma pretraining distribution.
4. **Text-to-code for "creative" websites is ill-posed — and the teams that solved the fidelity version all pivoted to screenshot-to-code or multimodal input.** The Awwwards judging criteria (Design 40%, Creativity 20%) are explicitly subjective and, by published statements, jurors "immediately recognize AI-generated layouts" and exclude them. Text prompts under-specify creative intent; this is an inherent ceiling of the problem formulation, not a training bug.
5. **The Stage 3 "GRPO with render-in-loop" plan is directionally real (VisRefiner does this exact thing) but will NOT bridge the creative gap. It will bridge a layout-fidelity gap.** Best-case outcome: Cipher produces cleaner, more renderable, slightly-more-on-brief HTML. It will not become Awwwards-caliber because the reward signal (CLIP similarity, render correctness) does not encode "creative taste."

---

## Where We're Wrong (if we are)

### 1. The core premise is wrong
The assumption was: "A well-fine-tuned 31B can reach Claude-quality creative output on this narrow task."

The data says otherwise:
- Vercel, the company with the most pressure and resources to do exactly this, **chose not to fine-tune**. They built a composite architecture around Claude Sonnet with a small autofixer model. The autofixer is ~fine-tuned; the creative brain is frontier-model-prompted.
- No open-source project has demonstrated Awwwards-caliber output from a sub-70B fine-tune. The best open research (ReLook at 7B) measures pixel fidelity on toy benchmarks.
- Fine-tuning small models closes gaps on **narrow, well-defined tasks** (the HuggingFace/Gemma literature is consistent). "Awwwards-quality creative site" is the opposite of narrow — it is open-ended, subjective, and taste-driven.

### 2. The data is wrong in ways that matter
- 54 records is below the "generalization threshold" in every PEFT study — which is fine, because the issue here is not quantity, it is provenance. Synthetic data written by an AI (you prompting Claude to write templates) teaches the model the AI's distribution, not the target distribution. You are essentially distilling Claude *through your prompting taste* into Gemma. The output ceiling is "slightly worse than what Claude would produce from your prompts."
- The 96 actual SOTD winners are sitting there, unused as training signal. They are the only real aesthetic grounding you have. A stage that doesn't use them isn't being truthful to the goal.

### 3. Text-to-code is the wrong task framing for this goal
- Awwwards jurors evaluate Design (40%), Usability (30%), Creativity (20%), Content (10%). Three of four criteria are visual/interactive, not textual.
- A text prompt like "build me a creative site for a coffee brand" has thousands of valid interpretations. The model cannot infer "do this specific scroll-locked-horizontal-marquee thing that Lusion ships" from text alone. Screenshot-to-code (Design2Code, WebSight, Pix2Struct) is a well-posed problem. Text-to-creative-code is not.

### 4. SimPO anti-slop SFT before you had a base model worth preferring over
SimPO preference pairs require a reference model whose outputs you can systematically beat. With a Gemma base and hand-crafted "good vs bad" pairs, you are teaching "avoid these anti-patterns" — a negative constraint. Negative constraints don't produce creative output; they prevent bad output. You cannot RL your way from generic-clean to creative-distinctive with anti-slop alone.

---

## Where We're Right (the parts worth keeping)

1. **Stage 1 SFT on frontend tutorials was fine.** This gave Gemma a modern HTML/CSS/JS baseline. Keep it.
2. **Motion library integration (Lenis + GSAP + ScrollTrigger) in the Stage 2.5 v2 output is genuinely hard and Cipher does it.** This is a real technical floor capability that most tutorial-trained models lack. Valuable for a narrower product.
3. **The diagnosis that v1 memorized and v2 is too generic is correct and sharp.** Final loss 0.2553 on 54 diverse records with syntactically clean 12-19KB output means the model IS learning structure, just not taste. That's a diagnostically useful data point.
4. **Render-in-loop GRPO is the right direction *for the right problem*.** If the product is "produce technically-correct, renderable, interactive scaffolding with good motion" — GRPO against render-success + CLS + no-console-errors is a real reward signal. The problem is you're mentally targeting "creative taste" and that reward signal doesn't encode taste.
5. **Having a local model at all is strategically valuable** — latency, cost, offline — but only once you accept it will not be the creative brain.

---

## The 3 Real Options Forward

### Option 1 — Scrap creative ambition. Become the scaffolding champion. (Recommended)

**What it is:** Reposition Cipher as a **technically excellent scaffolding model**. Narrow the problem: "Given a creative brief, produce a renderable, 15-25KB single-file HTML with Lenis + GSAP + ScrollTrigger correctly wired, semantic markup, WCAG-AA contrast, and zero console errors." The creative taste comes from a separate frontier-model pass that designers or Claude performs on top.

**Pros:**
- Cipher already does ~80% of this. Stage 3 GRPO with render + a11y + perf rewards (Lighthouse, axe-core) will genuinely push it to SOTA on this narrow task.
- Real reward signals. Not vibes.
- A 31B model CAN dominate this. Claude can't run on your laptop; Cipher can.
- Defensible product: "the fastest, cheapest, most reliable HTML scaffolder with motion."

**Cons:**
- You give up the Awwwards dream. Emotionally that hurts.
- It's a B2B tools pitch, not a "wow" demo.

**Expected outcome:** You ship a thing that is actually best-in-class at something real within 2–4 weeks.

---

### Option 2 — Drop the fine-tune. Ship a RAG-over-96-SOTD pipeline on top of Claude Opus / GPT-5.

**What it is:** Take the 96 real Awwwards SOTD sites. Index them (HTML structure, technique tags, effect library, screenshots as embeddings). Build a retrieval layer that, given a brief, pulls 3–5 most-stylistically-relevant SOTD sites and injects them as in-context examples to Claude Opus. This is literally what v0 does: curated in-context examples plus a frontier model.

**Pros:**
- Uses the SOTD data you actually have as **aesthetic grounding**, not training noise.
- No training. No GPU bills. No loss curves.
- Output quality = Claude Opus-quality + SOTD style conditioning. That's the real ceiling of what's achievable with current tech.
- Shippable in ~3 days.

**Cons:**
- No local model. Depends on Anthropic/OpenAI API.
- Less "cool." You aren't training anything.
- Per-request cost, not a one-time training cost.

**Expected outcome:** The output quality will be **meaningfully better than Cipher's current output** within a week, because you're starting from a 200B+ model that already has design priors baked in, and conditioning it on real SOTD references.

---

### Option 3 — Hybrid: Cipher as the drafter, Claude as the art director.

**What it is:** Keep Cipher for the fast local scaffolding pass (Option 1 product). Layer a Claude-Opus-based "art director" agent that takes Cipher's output + the SOTD RAG index and rewrites/enhances the creative aspects. Two-model pipeline.

**Pros:**
- Keeps the investment in Cipher meaningful.
- Plays to each model's strength: Cipher = speed + correctness, Claude = taste.
- Clearest product story: "local drafter, cloud director."

**Cons:**
- More engineering. Two models to maintain.
- Harder to debug which model caused which failure.
- You probably still don't win Awwwards — but you're now a tool agencies might actually buy.

**Expected outcome:** Best realistic quality ceiling. 6–8 weeks to first usable version.

---

## What Matt's Brother Would Say

"Dude. You've spent 2 days and it's producing clean-but-generic HTML. That is exactly what every fine-tuned small model on synthetic data produces. You are not a statistical outlier — you hit the predicted result of this approach. The teams who've spent millions on this problem — Vercel, Lovable, Anthropic's Artifacts team — all landed at the same answer: use the frontier model for creativity and fine-tune narrow sub-models for correctness. They did not train a 31B creative brain because they figured out it doesn't work.

You have 96 real Awwwards sites. That's gold. Use them as **retrieval references**, not as training data to distill into a smaller model that can't hold their richness anyway. Ship Option 2 in 72 hours. Keep Cipher on the shelf; it might be useful for Option 3 later.

The 2 days aren't wasted. You learned:
- Fine-tuning Gemma works mechanically (pipeline runs, loss drops, model trains).
- Small synthetic datasets produce clean but uncreative output. That's a known result, now proven in your hands.
- Motion library integration is a real capability you built.

Most importantly: you now know the ceiling. You can only reach it by stacking tools, not by training a bigger local model. Monday morning: start the RAG pipeline over the 96 SOTD sites. By Wednesday you'll have something that looks better than Cipher ever will."

---

## Sources

- [v0 Composite Model Family — Vercel Engineering](https://vercel.com/blog/v0-composite-model-family)
- [How we made v0 an effective coding agent — Vercel](https://vercel.com/blog/how-we-made-v0-an-effective-coding-agent)
- [Leaked system prompts from Vercel v0 — Simon Willison](https://simonwillison.net/2024/Nov/25/leaked-system-prompts-from-vercel-v0/)
- [System prompts and models of AI tools (x1xhlol)](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)
- [ReLook: Vision-Grounded RL with a Multimodal LLM Critic for Agentic Web Coding (arXiv 2510.11498)](https://arxiv.org/abs/2510.11498)
- [VisRefiner: Learning from Visual Differences for Screenshot-to-Code Generation (arXiv 2602.05998)](https://arxiv.org/abs/2602.05998)
- [Design2Code: Benchmarking Multimodal Code Generation (arXiv 2403.03163)](https://arxiv.org/pdf/2403.03163)
- [WebSight: Unlocking the conversion of Web Screenshots into HTML Code (arXiv 2403.09029)](https://arxiv.org/pdf/2403.09029)
- [Waffle: Fine-tuning Multi-Modal Models for Automated Front-End Development (arXiv 2410.18362)](https://arxiv.org/html/2410.18362)
- [Awwwards Site of the Day judging criteria — Utsubo](https://www.utsubo.com/blog/award-winning-website-design-guide)
- [Model collapse and synthetic data — TechTarget](https://www.techtarget.com/whatis/feature/Model-collapse-explained-How-synthetic-training-data-breaks-AI)
- [Distillation in Practice: Fine-tuning Gemma 3 27B — HuggingFace Blog](https://huggingface.co/blog/tawnymanticore/gemma3-ablations)
- [Customizing LLM Generation Style using PEFT (arXiv 2409.04574)](https://arxiv.org/html/2409.04574v1)
- [Fireworks AI x Vercel: Reinforcement Fine-Tuning for AutoFix](https://fireworks.ai/blog/vercel)
- [Fine-Tuning on Small Datasets — AIcompetence](https://aicompetence.org/fine-tuning-on-small-datasets/)
