/**
 * The Kraken Sees — Generate → Render → Critique → Iterate orchestrator.
 *
 * This is Cipher's USP. Wires together:
 *   - inference.ts       → local 31B (kin-cipher via Ollama) is the GENERATOR
 *   - render-loop.ts     → Playwright + axe-core quality harness
 *   - visual-critic      → frontier VLM (Claude/GPT Vision) scores screenshots
 *                          This is the "20% escalation" per kin-training README.
 *
 * Flow per call:
 *   1. Cipher (local) generates a single-file HTML from the brief.
 *   2. render-loop.ts headless-renders it, captures 3 viewports, runs axe-core.
 *   3. If quality < threshold:
 *        a. Ship the desktop screenshot + critique to the frontier VLM (Claude Vision).
 *        b. Feed the critique back into Cipher as an iteration request.
 *        c. Go to step 2.
 *   4. Return best render + final HTML.
 *
 * Per repo architecture, the generator is local. Frontier is used only for the
 * critic role, which per the README is the 20% escalation budget.
 *
 * @module companions/cipher/runtime/kraken-sees
 */

import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { CipherRenderLoop, type RenderResult, type RenderConfig } from './render-loop.js';

// ============================================================================
// Types
// ============================================================================

/** Generator callable — wraps whatever produces HTML from a prompt. */
export type HtmlGenerator = (args: {
  system: string;
  user: string;
  /** Optional additional context (e.g. previous critique) appended after user */
  context?: string;
  /** Optional temperature override */
  temperature?: number;
}) => Promise<string>;

/** Visual critic callable — judges a rendered screenshot. */
export type VisualCritic = (args: {
  /** Absolute path to a PNG screenshot */
  screenshotPath: string;
  /** Original brief (so the critic knows the intent) */
  brief: string;
  /** Previous critique to avoid repeating notes */
  previousCritique?: string;
}) => Promise<VisualCritiqueResult>;

export interface VisualCritiqueResult {
  /** 0-1 overall design score */
  designScore: number;
  /** 0-1 typography score */
  typographyScore: number;
  /** 0-1 layout/composition score */
  layoutScore: number;
  /** 0-1 motion/interactivity hints score (from what's statically visible) */
  craftScore: number;
  /** Human-readable critique delivered back to Cipher for the next iteration */
  critique: string;
  /** Whether the critic says ship-it */
  passes: boolean;
}

export interface KrakenSeesConfig {
  /** Min overall score (0-1) required to stop iterating. */
  qualityThreshold: number;
  /** Max iterations before we ship the best one even if threshold not met. */
  maxIterations: number;
  /** Directory for artifacts (HTML + screenshots). */
  outputDir: string;
  /** Render-loop config override */
  renderConfig?: Partial<RenderConfig>;
  /** Whether to skip visual critic when render score is already high. */
  skipCritiqueAboveRenderScore: number;
}

export interface KrakenSeesResult {
  /** Final HTML that shipped */
  html: string;
  /** All iterations captured (for inspection) */
  iterations: IterationRecord[];
  /** Did we hit the quality bar? */
  passedThreshold: boolean;
  /** Total wall time in ms */
  latencyMs: number;
  /** Path to the final HTML file */
  htmlPath: string;
  /** Path to the final desktop screenshot */
  screenshotPath: string | null;
}

export interface IterationRecord {
  iteration: number;
  html: string;
  htmlPath: string;
  render: RenderResult;
  critique: VisualCritiqueResult | null;
  compositeScore: number;
}

// ============================================================================
// Default Config
// ============================================================================

const DEFAULT_CONFIG: KrakenSeesConfig = {
  qualityThreshold: 0.8,
  maxIterations: 3,
  outputDir: 'out/kraken-sees',
  skipCritiqueAboveRenderScore: 0.92,
};

// ============================================================================
// Orchestrator
// ============================================================================

export class KrakenSees {
  private config: KrakenSeesConfig;
  private renderLoop: CipherRenderLoop;
  private generator: HtmlGenerator;
  private critic: VisualCritic | null;

  constructor(opts: {
    generator: HtmlGenerator;
    critic?: VisualCritic | null;
    config?: Partial<KrakenSeesConfig>;
  }) {
    this.config = { ...DEFAULT_CONFIG, ...opts.config };
    this.generator = opts.generator;
    this.critic = opts.critic ?? null;
    this.renderLoop = new CipherRenderLoop(this.config.renderConfig);
    mkdirSync(this.config.outputDir, { recursive: true });
  }

  /**
   * Build a site end-to-end: generate, render, critique, iterate.
   */
  async build(args: {
    /** Identifier used for output folder names */
    siteId: string;
    /** System prompt (Cipher persona + hard rules) */
    system: string;
    /** The brief (what to build) */
    user: string;
  }): Promise<KrakenSeesResult> {
    const t0 = Date.now();
    const siteDir = join(this.config.outputDir, args.siteId);
    mkdirSync(siteDir, { recursive: true });

    const iterations: IterationRecord[] = [];
    let runningCritique: string | undefined;

    for (let i = 0; i < this.config.maxIterations; i++) {
      const iterNum = i + 1;
      const iterDir = join(siteDir, `iter-${iterNum}`);
      mkdirSync(iterDir, { recursive: true });

      // ── 1. Generate ────────────────────────────────────────────────────
      const html = await this.generator({
        system: args.system,
        user: args.user,
        context: runningCritique,
        // First pass: more diverse; subsequent passes: focused on fixing notes
        temperature: i === 0 ? 0.8 : 0.55,
      });

      const htmlPath = join(iterDir, 'site.html');
      writeFileSync(htmlPath, html, 'utf-8');

      // ── 2. Render + axe audit ──────────────────────────────────────────
      const render = await this.renderLoop.renderHTML(html, {
        renderId: `${args.siteId}-iter-${iterNum}`,
      });

      // ── 3. Visual critique (only if render score not already great) ────
      let critique: VisualCritiqueResult | null = null;
      if (
        this.critic &&
        render.qualityScore < this.config.skipCritiqueAboveRenderScore
      ) {
        const desktopShot = render.screenshots.find((s) => s.viewport === 'desktop');
        if (desktopShot) {
          critique = await this.critic({
            screenshotPath: desktopShot.path,
            brief: args.user,
            previousCritique: runningCritique,
          });
        }
      }

      // Composite score: render is 40%, visual critic (if present) is 60%.
      // If no critic is available we fall back to render score as ground truth.
      const compositeScore = critique
        ? 0.4 * render.qualityScore +
          0.6 *
            (0.35 * critique.designScore +
              0.25 * critique.typographyScore +
              0.25 * critique.layoutScore +
              0.15 * critique.craftScore)
        : render.qualityScore;

      iterations.push({
        iteration: iterNum,
        html,
        htmlPath,
        render,
        critique,
        compositeScore,
      });

      // Write an iteration report
      writeFileSync(
        join(iterDir, 'report.json'),
        JSON.stringify(
          {
            iteration: iterNum,
            compositeScore,
            render: {
              qualityScore: render.qualityScore,
              passesThreshold: render.passesThreshold,
              accessibility: render.accessibility,
              latencyMs: render.latencyMs,
              screenshots: render.screenshots.map((s) => s.path),
            },
            critique,
          },
          null,
          2,
        ),
      );

      // ── 4. Stop if we cleared the bar ──────────────────────────────────
      if (compositeScore >= this.config.qualityThreshold) {
        break;
      }

      // ── 5. Otherwise, feed critique back into next generation ──────────
      runningCritique = buildIterationContext({
        priorCritique: runningCritique,
        render,
        critique,
      });
    }

    // Pick the best iteration (highest composite) as the shipped result
    const best = iterations.reduce((acc, cur) =>
      cur.compositeScore > acc.compositeScore ? cur : acc,
    );

    // Copy the winning HTML + desktop screenshot into the siteDir root
    const finalHtmlPath = join(siteDir, 'final.html');
    writeFileSync(finalHtmlPath, best.html, 'utf-8');
    const finalShot =
      best.render.screenshots.find((s) => s.viewport === 'desktop')?.path ?? null;

    return {
      html: best.html,
      iterations,
      passedThreshold: best.compositeScore >= this.config.qualityThreshold,
      latencyMs: Date.now() - t0,
      htmlPath: finalHtmlPath,
      screenshotPath: finalShot,
    };
  }

  async close(): Promise<void> {
    await this.renderLoop.close();
  }
}

// ============================================================================
// Iteration-context builder (structured feedback Cipher can act on)
// ============================================================================

function buildIterationContext(args: {
  priorCritique?: string;
  render: RenderResult;
  critique: VisualCritiqueResult | null;
}): string {
  const lines: string[] = [];
  lines.push('---');
  lines.push('PREVIOUS ITERATION CRITIQUE:');
  lines.push('');

  if (args.priorCritique) {
    lines.push('(Notes still outstanding from earlier iteration:)');
    lines.push(args.priorCritique.slice(0, 800));
    lines.push('');
  }

  const axe = args.render.accessibility;
  if (axe) {
    if (axe.critical > 0 || axe.serious > 0) {
      lines.push(
        `Accessibility: ${axe.critical} critical + ${axe.serious} serious WCAG violations.`,
      );
      axe.details.slice(0, 5).forEach((v) => {
        lines.push(` - [${v.impact}] ${v.id}: ${v.help} (${v.nodes} nodes)`);
      });
    }
  }

  if (args.critique) {
    lines.push('');
    lines.push(
      `Visual scores — design ${args.critique.designScore.toFixed(2)}, typography ${args.critique.typographyScore.toFixed(2)}, layout ${args.critique.layoutScore.toFixed(2)}, craft ${args.critique.craftScore.toFixed(2)}.`,
    );
    lines.push('');
    lines.push('Detailed critique (fix these in the next version):');
    lines.push(args.critique.critique);
  } else {
    lines.push('');
    lines.push(args.render.critique);
  }

  lines.push('');
  lines.push(
    'Produce a revised COMPLETE single-file HTML that addresses the notes above. ' +
      'Keep what worked. Do not regress on any quality dimension. Output ONLY the HTML.',
  );
  lines.push('---');

  return lines.join('\n');
}

// ============================================================================
// Concrete adapters
// ============================================================================

/**
 * Ollama generator adapter — talks to local Ollama at /api/generate.
 * This wires the local 31B Cipher in as the GENERATOR per Kin architecture.
 */
export function ollamaGenerator(opts: {
  apiUrl: string;
  model: string;
  maxTokens?: number;
  contextWindow?: number;
}): HtmlGenerator {
  return async ({ system, user, context, temperature }) => {
    const prompt = context
      ? `${system}\n\n${user}\n\n${context}`
      : `${system}\n\n${user}`;

    const body = {
      model: opts.model,
      prompt: `<start_of_turn>user\n${prompt}<end_of_turn>\n<start_of_turn>model\n`,
      stream: false,
      raw: true,
      options: {
        temperature: temperature ?? 0.75,
        top_p: 0.9,
        repeat_penalty: 1.05,
        num_predict: opts.maxTokens ?? 8192,
        num_ctx: opts.contextWindow ?? 16384,
        stop: ['<end_of_turn>', '<start_of_turn>'],
      },
    };

    const res = await fetch(`${opts.apiUrl.replace(/\/$/, '')}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`Ollama generate failed: ${res.status} ${await res.text()}`);
    }

    const json = (await res.json()) as { response?: string };
    const raw = json.response ?? '';
    return extractHtml(raw);
  };
}

/**
 * Anthropic Claude visual critic adapter.
 *
 * Sends the desktop screenshot + brief to Claude Vision and asks for scored
 * critique. Per Kin architecture, this is used as the 20% "frontier supervisor"
 * escalation — NOT as the generator.
 */
export function claudeVisualCritic(opts: {
  apiKey: string;
  model?: string;
  apiUrl?: string;
}): VisualCritic {
  const apiUrl = opts.apiUrl ?? 'https://api.anthropic.com/v1/messages';
  const model = opts.model ?? 'claude-sonnet-4-20250514';

  return async ({ screenshotPath, brief, previousCritique }) => {
    if (!existsSync(screenshotPath)) {
      throw new Error(`Screenshot not found: ${screenshotPath}`);
    }
    const imageB64 = readFileSync(screenshotPath).toString('base64');

    const systemPrompt =
      'You are an Awwwards juror scoring a website screenshot. ' +
      'Score strictly on Awwwards criteria: Design (40%), Usability (30%), Creativity (20%), Content (10%). ' +
      'Return ONLY compact JSON with keys: designScore, typographyScore, layoutScore, craftScore (all 0-1), critique (string, <=400 chars, specific and actionable), passes (bool).';

    const userText = [
      `Brief: ${brief}`,
      previousCritique
        ? `\nPrevious critique (check if addressed): ${previousCritique.slice(0, 600)}`
        : '',
      '\nLook hard at: typography hierarchy, whitespace composition, color coherence, section rhythm, and whether the hero actually feels like the site, not a template.',
      '\nReturn ONLY JSON.',
    ].join('');

    const body = {
      model,
      max_tokens: 600,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'image',
              source: { type: 'base64', media_type: 'image/png', data: imageB64 },
            },
            { type: 'text', text: userText },
          ],
        },
      ],
    };

    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'x-api-key': opts.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`Claude critic failed: ${res.status} ${await res.text()}`);
    }

    const json = (await res.json()) as {
      content?: Array<{ type: string; text?: string }>;
    };
    const text = json.content?.find((c) => c.type === 'text')?.text ?? '';
    const parsed = parseCritiqueJson(text);
    return parsed;
  };
}

// ============================================================================
// Helpers
// ============================================================================

function extractHtml(raw: string): string {
  // Strip chat tokens Cipher sometimes leaks
  let s = raw.replace(/<\/?start_of_turn>[^\n]*/g, '').replace(/<\/?end_of_turn>[^\n]*/g, '');
  // Pull fenced block if present
  const fence = s.match(/```(?:html)?\s*\n?([\s\S]*?)```/);
  if (fence) s = fence[1];
  // Trim preamble before <!DOCTYPE or <html
  const idx = s.search(/<!DOCTYPE|<html/i);
  if (idx > 0) s = s.slice(idx);
  return s.trim();
}

function parseCritiqueJson(text: string): VisualCritiqueResult {
  // Critic sometimes wraps in prose; extract the first JSON object.
  const m = text.match(/\{[\s\S]*\}/);
  const blob = m ? m[0] : text;
  try {
    const j = JSON.parse(blob);
    const clip = (n: unknown): number => {
      const v = typeof n === 'number' ? n : Number(n);
      if (!isFinite(v)) return 0.5;
      return Math.max(0, Math.min(1, v));
    };
    return {
      designScore: clip(j.designScore),
      typographyScore: clip(j.typographyScore),
      layoutScore: clip(j.layoutScore),
      craftScore: clip(j.craftScore),
      critique: String(j.critique ?? '').slice(0, 800),
      passes: Boolean(j.passes),
    };
  } catch {
    // Fallback: middle-of-road scores so the loop keeps moving instead of erroring.
    return {
      designScore: 0.5,
      typographyScore: 0.5,
      layoutScore: 0.5,
      craftScore: 0.5,
      critique: text.slice(0, 400) || 'Critic returned unparseable output.',
      passes: false,
    };
  }
}
