/**
 * Kraken Sees CLI — end-to-end runner for Cipher's render-critique-iterate loop.
 *
 * Usage:
 *   CIPHER_API_URL=http://127.0.0.1:11500 \
 *   CIPHER_MODEL=kin-cipher-31b \
 *   ANTHROPIC_API_KEY=... \
 *   npx tsx companions/cipher/runtime/kraken-sees-cli.ts \
 *     --brief "Build an architecture studio portfolio for Meridian Studio..." \
 *     --site-id meridian \
 *     --out out/kraken/meridian
 *
 * Env:
 *   CIPHER_API_URL       Ollama base URL (default http://127.0.0.1:11500)
 *   CIPHER_MODEL         Ollama model name (default kin-cipher-31b)
 *   ANTHROPIC_API_KEY    Claude API key (optional — if absent, no visual critic)
 *   CIPHER_CRITIC_MODEL  Claude model id (default claude-sonnet-4-20250514)
 *
 * No Claude API key? The loop still runs — it just relies on render-loop.ts's
 * axe-core + heuristic score instead of visual critique. That's still better
 * than a one-shot model.
 *
 * @module companions/cipher/runtime/kraken-sees-cli
 */

import { readFileSync, existsSync } from 'fs';
import { KrakenSees, ollamaGenerator, claudeVisualCritic, type HtmlGenerator, type VisualCritic } from './kraken-sees.js';

// ============================================================================
// CLI args
// ============================================================================

interface Args {
  brief: string;
  siteId: string;
  out: string;
  system?: string;
  maxIterations: number;
  threshold: number;
}

function parseArgs(argv: string[]): Args {
  const get = (key: string): string | undefined => {
    const idx = argv.indexOf(`--${key}`);
    return idx >= 0 ? argv[idx + 1] : undefined;
  };
  const brief = get('brief');
  const siteId = get('site-id') ?? 'site';
  const out = get('out') ?? `out/kraken/${siteId}`;
  const system = get('system');
  const maxIterations = Number(get('max-iterations') ?? '3');
  const threshold = Number(get('threshold') ?? '0.8');

  if (!brief) {
    console.error('Missing --brief.');
    process.exit(2);
  }
  return { brief, siteId, out, system, maxIterations, threshold };
}

// ============================================================================
// Default system prompt (Cipher's Awwwards hard rules)
// ============================================================================

const DEFAULT_SYSTEM = [
  'You are Cipher, the Code Kraken.',
  'Build COMPLETE Awwwards-quality single-file HTML.',
  '',
  'HARD RULES:',
  '- NO Tailwind. Vanilla CSS only. Use :root custom properties + clamp() for type.',
  '- Motion stack: Lenis (autoRaf: true), GSAP, ScrollTrigger, SplitText — CDN inline.',
  '- Do NOT call lenis.stop().',
  '- Parents stay opacity:1. Only animate children.',
  '- Never reference DOM ids that do not exist.',
  '- All content visible on first paint.',
  '- Serif-display + sans-body pairing (Fraunces/Playfair + Inter).',
  '- Semantic HTML: <header>, <main>, <section>, <article>, <nav>, <footer>.',
  '- Images: https://picsum.photos/seed/{label}/{w}/{h}.',
  '',
  'Output ONLY the HTML starting with <!DOCTYPE html>. No preamble, no fences.',
].join('\n');

// ============================================================================
// Runner
// ============================================================================

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const apiUrl = process.env.CIPHER_API_URL ?? 'http://127.0.0.1:11500';
  const model = process.env.CIPHER_MODEL ?? 'kin-cipher-31b';
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  const criticModel = process.env.CIPHER_CRITIC_MODEL ?? 'claude-sonnet-4-20250514';

  // System prompt — load from --system file if given, else default
  const system = args.system && existsSync(args.system)
    ? readFileSync(args.system, 'utf-8')
    : DEFAULT_SYSTEM;

  // Generator — local Ollama 31B (this is what makes it Kin, not a ChatGPT wrapper)
  const generator: HtmlGenerator = ollamaGenerator({ apiUrl, model });

  // Critic — Claude Vision if we have a key, otherwise run without
  let critic: VisualCritic | null = null;
  if (anthropicKey) {
    critic = claudeVisualCritic({ apiKey: anthropicKey, model: criticModel });
  } else {
    console.warn(
      '[warn] ANTHROPIC_API_KEY not set — running WITHOUT visual critic. ' +
      'Quality scoring will come from render-loop (axe + heuristic) only.',
    );
  }

  const kraken = new KrakenSees({
    generator,
    critic,
    config: {
      outputDir: args.out,
      maxIterations: args.maxIterations,
      qualityThreshold: args.threshold,
    },
  });

  console.log('--- The Kraken Sees ---');
  console.log(`  generator:  ${apiUrl}  (model: ${model})`);
  console.log(`  critic:     ${critic ? 'Claude Vision (' + criticModel + ')' : 'none (render-loop only)'}`);
  console.log(`  site:       ${args.siteId}`);
  console.log(`  iterations: up to ${args.maxIterations}`);
  console.log(`  threshold:  ${args.threshold}`);
  console.log(`  out:        ${args.out}`);
  console.log('');

  const t0 = Date.now();
  const result = await kraken.build({
    siteId: args.siteId,
    system,
    user: args.brief,
  });

  const totalSec = ((Date.now() - t0) / 1000).toFixed(1);
  console.log('--- done ---');
  console.log(`  iterations run: ${result.iterations.length}`);
  result.iterations.forEach((it) => {
    const axe = it.render.accessibility;
    console.log(
      `  iter ${it.iteration}: composite=${it.compositeScore.toFixed(3)} ` +
      `render=${it.render.qualityScore.toFixed(3)} ` +
      `axe=${axe ? `${axe.violations}v (${axe.critical}c/${axe.serious}s)` : 'n/a'} ` +
      `${it.critique ? `design=${it.critique.designScore.toFixed(2)}` : ''}`,
    );
  });
  console.log(`  passed threshold: ${result.passedThreshold}`);
  console.log(`  wall time: ${totalSec}s`);
  console.log(`  final html: ${result.htmlPath}`);
  if (result.screenshotPath) {
    console.log(`  final screenshot: ${result.screenshotPath}`);
  }

  await kraken.close();
}

main().catch((err) => {
  console.error('Kraken Sees crashed:', err);
  process.exit(1);
});
