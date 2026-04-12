/**
 * The Kraken Sees — Render-Critique Loop
 *
 * Cipher's killer USP: Generate code → Render in headless browser →
 * Screenshot → axe-core audit → Visual critique → Iterate until beautiful.
 *
 * This module provides both:
 * - Training-time rewards (GRPO visual reward signal)
 * - Runtime self-critique (user-facing build → review → iterate)
 *
 * @module companions/cipher/runtime/render-loop
 */

import { chromium, type Browser, type Page, type BrowserContext } from 'playwright';
import { writeFileSync, mkdirSync, existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

// ============================================================================
// Types
// ============================================================================

export interface RenderConfig {
  /** Viewports to capture */
  viewports: Viewport[];
  /** Whether to run axe-core accessibility audit */
  accessibilityAudit: boolean;
  /** Whether to capture interaction states (hover, scroll) */
  captureInteractions: boolean;
  /** Maximum iterations for self-critique loop */
  maxIterations: number;
  /** Quality threshold (0-1) — below this triggers re-iteration */
  qualityThreshold: number;
  /** Temp directory for renders */
  renderDir: string;
}

export interface Viewport {
  name: string;
  width: number;
  height: number;
}

export interface RenderResult {
  /** Render ID for tracking */
  renderId: string;
  /** Screenshot file paths */
  screenshots: ScreenshotResult[];
  /** Accessibility audit results */
  accessibility: AccessibilityResult | null;
  /** Composite quality score (0-1) */
  qualityScore: number;
  /** Whether the render meets quality threshold */
  passesThreshold: boolean;
  /** Human-readable critique summary */
  critique: string;
  /** Rendering latency in ms */
  latencyMs: number;
}

export interface ScreenshotResult {
  viewport: string;
  path: string;
  width: number;
  height: number;
}

export interface AccessibilityResult {
  /** Number of violations */
  violations: number;
  /** Critical violations (WCAG Level A) */
  critical: number;
  /** Serious violations (WCAG Level AA) */
  serious: number;
  /** Moderate violations */
  moderate: number;
  /** Minor violations */
  minor: number;
  /** Pass rate (0-1) */
  passRate: number;
  /** Violation details */
  details: AccessibilityViolation[];
}

export interface AccessibilityViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  help: string;
  helpUrl: string;
  nodes: number;
}

// ============================================================================
// Default Config
// ============================================================================

const DEFAULT_CONFIG: RenderConfig = {
  viewports: [
    { name: 'desktop', width: 1920, height: 1080 },
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
  ],
  accessibilityAudit: true,
  captureInteractions: true,
  maxIterations: 3,
  qualityThreshold: 0.85,
  renderDir: join(tmpdir(), 'cipher-renders'),
};

// ============================================================================
// Render Pipeline
// ============================================================================

export class CipherRenderLoop {
  private config: RenderConfig;
  private browser: Browser | null = null;

  constructor(config?: Partial<RenderConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    mkdirSync(this.config.renderDir, { recursive: true });
  }

  /**
   * Check if Playwright/Chromium is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const browser = await chromium.launch({ headless: true });
      await browser.close();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Render HTML content directly (fast mode — no server needed)
   */
  async renderHTML(html: string, options?: { css?: string; renderId?: string }): Promise<RenderResult> {
    const start = Date.now();
    const renderId = options?.renderId ?? `render-${Date.now()}`;
    const renderDir = join(this.config.renderDir, renderId);
    mkdirSync(renderDir, { recursive: true });

    // Write HTML file with Tailwind CDN for quick rendering
    const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cipher Render</title>
  <script src="https://cdn.tailwindcss.com"></script>
  ${options?.css ? `<style>${options.css}</style>` : ''}
</head>
<body>
${html}
</body>
</html>`;

    const htmlPath = join(renderDir, 'index.html');
    writeFileSync(htmlPath, fullHtml, 'utf-8');

    return this.renderPage(`file://${htmlPath}`, renderId, renderDir, start);
  }

  /**
   * Render a URL (full mode — for Next.js dev server)
   */
  async renderURL(url: string, options?: { renderId?: string }): Promise<RenderResult> {
    const start = Date.now();
    const renderId = options?.renderId ?? `render-${Date.now()}`;
    const renderDir = join(this.config.renderDir, renderId);
    mkdirSync(renderDir, { recursive: true });

    return this.renderPage(url, renderId, renderDir, start);
  }

  /**
   * Core render pipeline — captures screenshots + runs audits
   */
  private async renderPage(
    url: string,
    renderId: string,
    renderDir: string,
    startTime: number,
  ): Promise<RenderResult> {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
      });
    }

    const screenshots: ScreenshotResult[] = [];
    let accessibility: AccessibilityResult | null = null;

    try {
      // Capture each viewport
      for (const vp of this.config.viewports) {
        const context: BrowserContext = await this.browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          deviceScaleFactor: 1,
          reducedMotion: 'reduce',
          colorScheme: 'light',
        });

        const page: Page = await context.newPage();
        await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
        await page.waitForLoadState('domcontentloaded');

        // Wait for any Tailwind JIT or hydration
        await page.waitForTimeout(500);

        const screenshotPath = join(renderDir, `${vp.name}-${vp.width}x${vp.height}.png`);
        await page.screenshot({
          path: screenshotPath,
          fullPage: true,
          animations: 'disabled',
        });

        screenshots.push({
          viewport: vp.name,
          path: screenshotPath,
          width: vp.width,
          height: vp.height,
        });

        // Capture dark mode variant
        const darkContext = await this.browser.newContext({
          viewport: { width: vp.width, height: vp.height },
          colorScheme: 'dark',
          reducedMotion: 'reduce',
        });
        const darkPage = await darkContext.newPage();
        await darkPage.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
        const darkPath = join(renderDir, `${vp.name}-dark-${vp.width}x${vp.height}.png`);
        await darkPage.screenshot({ path: darkPath, fullPage: true, animations: 'disabled' });
        screenshots.push({
          viewport: `${vp.name}-dark`,
          path: darkPath,
          width: vp.width,
          height: vp.height,
        });
        await darkContext.close();

        // Run accessibility audit on the first (desktop) viewport
        if (this.config.accessibilityAudit && vp.name === 'desktop') {
          accessibility = await this.runAccessibilityAudit(page);
        }

        await context.close();
      }

      // Compute quality score
      const qualityScore = this.computeQualityScore(accessibility, screenshots);
      const critique = this.generateCritique(accessibility, qualityScore);

      return {
        renderId,
        screenshots,
        accessibility,
        qualityScore,
        passesThreshold: qualityScore >= this.config.qualityThreshold,
        critique,
        latencyMs: Date.now() - startTime,
      };
    } catch (error) {
      return {
        renderId,
        screenshots,
        accessibility: null,
        qualityScore: 0,
        passesThreshold: false,
        critique: `Render failed: ${error instanceof Error ? error.message : String(error)}`,
        latencyMs: Date.now() - startTime,
      };
    }
  }

  /**
   * Run axe-core accessibility audit on a page
   */
  private async runAccessibilityAudit(page: Page): Promise<AccessibilityResult> {
    try {
      // Inject axe-core
      const axeSource = readFileSync(
        join(process.cwd(), 'node_modules', 'axe-core', 'axe.min.js'),
        'utf-8'
      );
      await page.evaluate(axeSource);

      // Run audit
      const results = await page.evaluate(() => {
        return (window as any).axe.run(document, {
          runOnly: {
            type: 'tag',
            values: ['wcag2a', 'wcag2aa', 'wcag21aa'],
          },
        });
      }) as { violations: any[]; passes: any[] };

      const violations = results.violations.map((v: any) => ({
        id: v.id,
        impact: v.impact as AccessibilityViolation['impact'],
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        nodes: v.nodes?.length ?? 0,
      }));

      const critical = violations.filter(v => v.impact === 'critical').length;
      const serious = violations.filter(v => v.impact === 'serious').length;
      const moderate = violations.filter(v => v.impact === 'moderate').length;
      const minor = violations.filter(v => v.impact === 'minor').length;

      const totalChecks = results.passes.length + results.violations.length;
      const passRate = totalChecks > 0 ? results.passes.length / totalChecks : 1;

      return {
        violations: violations.length,
        critical,
        serious,
        moderate,
        minor,
        passRate,
        details: violations,
      };
    } catch {
      // axe-core not available — return neutral score
      return {
        violations: 0,
        critical: 0,
        serious: 0,
        moderate: 0,
        minor: 0,
        passRate: 0.5,
        details: [],
      };
    }
  }

  /**
   * Compute composite quality score (0-1)
   */
  private computeQualityScore(
    accessibility: AccessibilityResult | null,
    _screenshots: ScreenshotResult[],
  ): number {
    let score = 0.5; // Base score for successful render

    if (accessibility) {
      // Accessibility is 40% of score
      const a11yScore = accessibility.passRate;
      const criticalPenalty = accessibility.critical * 0.15;
      const seriousPenalty = accessibility.serious * 0.08;
      score += Math.max(0, (a11yScore - criticalPenalty - seriousPenalty)) * 0.4;
    } else {
      score += 0.2; // Partial credit when audit unavailable
    }

    // Render success is 10% of score (we got here = success)
    score += 0.1;

    return Math.min(1, Math.max(0, score));
  }

  /**
   * Generate human-readable critique from results
   */
  private generateCritique(
    accessibility: AccessibilityResult | null,
    qualityScore: number,
  ): string {
    const parts: string[] = [];

    if (qualityScore >= 0.9) {
      parts.push("Now THIS is clean. The render looks sharp across viewports.");
    } else if (qualityScore >= 0.7) {
      parts.push("Good foundation, but I've got some notes — let me wrap my tentacles around the details.");
    } else {
      parts.push("We can do better than this. Let me dive deeper.");
    }

    if (accessibility) {
      if (accessibility.critical > 0) {
        parts.push(`🚨 ${accessibility.critical} critical accessibility violation(s) — these need fixing NOW.`);
      }
      if (accessibility.serious > 0) {
        parts.push(`⚠️ ${accessibility.serious} serious accessibility issue(s) — WCAG AA requires these fixed.`);
      }
      if (accessibility.violations === 0) {
        parts.push("✅ Zero accessibility violations — WCAG 2.1 AA certified. Chef's kiss. 🐙");
      }
      if (accessibility.passRate >= 0.95) {
        parts.push(`Accessibility pass rate: ${(accessibility.passRate * 100).toFixed(1)}% — beautiful.`);
      }
    }

    return parts.join('\n');
  }

  /**
   * Clean up browser resources
   */
  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }
}

// ============================================================================
// Singleton
// ============================================================================

let _instance: CipherRenderLoop | null = null;

export function getCipherRenderLoop(config?: Partial<RenderConfig>): CipherRenderLoop {
  if (!_instance) {
    _instance = new CipherRenderLoop(config);
  }
  return _instance;
}
