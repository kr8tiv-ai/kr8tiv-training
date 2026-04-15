"""Generate 3 Awwwards-quality website examples with Cipher SFT (via Unsloth)."""
import torch, re, os
from unsloth import FastLanguageModel

print("[1/4] Loading model with Unsloth (60GB - takes ~2min)...", flush=True)
model, tok = FastLanguageModel.from_pretrained(
    model_name="/content/cipher-sft-merged",
    max_seq_length=8192,
    load_in_4bit=True,
    dtype=None,
)
FastLanguageModel.for_inference(model)
print("[2/4] Model ready.", flush=True)

PROMPTS = {
    "01-hero-particles": "Build a complete single-file HTML page with a stunning hero section featuring a Three.js particle system that responds to mouse movement. Include CDN imports for Three.js (use https://unpkg.com/three@0.160.0/build/three.module.js with importmap). Use GSAP from CDN for the headline entrance animation. Style with custom CSS - dark theme with bioluminescent blue/purple accents (#9bf, #a4f). Include a headline 'Cipher.ai' and subheadline 'The Code Kraken sees what others miss.' Make it Awwwards-quality. Output ONLY the complete HTML, nothing else.",
    "02-portfolio-scroll": "Build a complete single-file HTML page that's a portfolio with smooth scrolling using Lenis from CDN. Include 3 project sections with parallax images and GSAP scroll-triggered text reveals. Dark elegant theme with custom serif typography. Use placeholder images from picsum.photos. Include CDN scripts inline. Output ONLY complete HTML.",
    "03-3d-card": "Build a complete single-file HTML page with an interactive 3D card that flips and rotates on mouse hover. Use vanilla JS with CSS 3D transforms. Glassmorphism style with backdrop-filter. Include subtle GSAP animations for entry. Make the card show a Cipher product preview. Output ONLY complete HTML.",
}

os.makedirs("/content/cipher-sites", exist_ok=True)
print("[3/4] Generating sites...", flush=True)

for name, prompt in PROMPTS.items():
    print(f"  -> {name}", flush=True)
    msgs = [
        {"role": "system", "content": "You are Cipher, the Code Kraken. Award-winning frontend AI. Output only complete HTML files starting with <!DOCTYPE html>, no markdown fences, no preamble."},
        {"role": "user", "content": prompt},
    ]
    inputs = tok.apply_chat_template(
        msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to("cuda")
    with torch.no_grad():
        out = model.generate(
            inputs, max_new_tokens=4096, do_sample=True,
            temperature=0.7, top_p=0.9, repetition_penalty=1.05,
            pad_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0][inputs.shape[1]:], skip_special_tokens=True)
    if "```" in text:
        m2 = re.search(r"```(?:html)?\s*\n?(.*?)```", text, re.DOTALL)
        if m2:
            text = m2.group(1)
    if "<!DOCTYPE" not in text and "<html" not in text:
        text = "<!DOCTYPE html><html><body><pre>" + text + "</pre></body></html>"
    with open(f"/content/cipher-sites/{name}.html", "w") as f:
        f.write(text)
    print(f"     saved ({len(text)} chars)", flush=True)

# Index page
with open("/content/cipher-sites/index.html", "w") as f:
    f.write("""<!DOCTYPE html><html><head><title>Cipher Generated Sites</title>
<style>body{font-family:system-ui;max-width:700px;margin:60px auto;padding:24px;background:#0a0a0f;color:#e8e8ff}
a{display:block;padding:24px;margin:14px 0;background:#1a1a2e;color:#9bf;text-decoration:none;border-radius:12px;border:1px solid #333;transition:all .2s}
a:hover{background:#252550;border-color:#9bf;transform:translateY(-2px)}
h1{color:#a4f;font-weight:300;letter-spacing:-1px}
.tag{font-size:11px;background:#252540;padding:4px 10px;border-radius:20px;display:inline-block;margin-left:8px;color:#9bf}</style></head><body>
<h1>Cipher - Generated Sites</h1>
<p style="color:#8888aa;margin-bottom:32px">Trained on Awwwards-quality code. Three.js, GSAP, Lenis.</p>
<a href="01-hero-particles.html">01. Hero with Three.js Particles<span class="tag">Three.js + GSAP</span></a>
<a href="02-portfolio-scroll.html">02. Smooth Scroll Portfolio<span class="tag">Lenis + GSAP</span></a>
<a href="03-3d-card.html">03. Interactive 3D Card<span class="tag">CSS 3D + GSAP</span></a>
</body></html>""")

print("[4/4] DONE - 3 sites in /content/cipher-sites/", flush=True)
