/**
 * Cipher Runtime Server — Fastify MCP server for the Code Kraken
 *
 * Exposes Cipher's capabilities via HTTP API:
 * - POST /api/chat — Send message, get response (local or frontier)
 * - POST /api/render — Render HTML and get screenshots + audit
 * - POST /api/critique — Run visual critique on existing screenshots
 * - GET  /api/health — Heartbeat check
 * - WS   /ws/chat — Streaming WebSocket chat
 *
 * Integrates with the existing KIN backend:
 * - Uses OllamaClient patterns from inference/local-llm.ts
 * - Follows FastifyPluginAsync route pattern from api/routes/
 * - Respects harness.yaml + openclaw.json security config
 *
 * @module companions/cipher/runtime/server
 */

import Fastify from 'fastify';
import cors from '@fastify/cors';
import { CipherInference } from './inference.js';
import { CipherRenderLoop } from './render-loop.js';

const PORT = parseInt(process.env.CIPHER_PORT ?? '3333', 10);
const HOST = process.env.CIPHER_HOST ?? '0.0.0.0';

// ============================================================================
// Server Setup
// ============================================================================

const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',
    transport: {
      target: 'pino-pretty',
      options: { colorize: true },
    },
  },
});

await app.register(cors, { origin: true });

// ============================================================================
// Instances
// ============================================================================

const cipher = new CipherInference();
const renderer = new CipherRenderLoop();

// ============================================================================
// Routes
// ============================================================================

/** Health check — heartbeat contract */
app.get('/api/health', async () => {
  const localAvailable = await cipher.isLocalAvailable();
  const renderAvailable = await renderer.isAvailable();
  const model = await cipher.resolveModel();

  return {
    status: localAvailable ? 'healthy' : 'degraded',
    companion: 'cipher',
    species: 'Code Kraken',
    emoji: '🐙',
    components: {
      local_brain: { available: localAvailable, model },
      render_loop: { available: renderAvailable, engine: 'playwright' },
      frontier: { configured: !!process.env.OPENROUTER_API_KEY },
      memory: { configured: !!process.env.SUPERMEMORY_API_KEY },
    },
    timestamp: new Date().toISOString(),
  };
});

/** Chat endpoint — send message, get Cipher response */
app.post<{
  Body: {
    message: string;
    images?: string[];
    forceLocal?: boolean;
    forceFrontier?: boolean;
    stream?: boolean;
  };
}>('/api/chat', async (request, reply) => {
  const { message, images, forceLocal, forceFrontier, stream } = request.body;

  if (!message?.trim()) {
    return reply.status(400).send({ error: 'Message is required' });
  }

  try {
    const result = await cipher.chat(message, {
      images,
      forceLocal,
      forceFrontier,
      stream,
    });

    return {
      content: result.content,
      route: result.route,
      model: result.model,
      latencyMs: result.latencyMs,
      tokens: result.tokens,
    };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return reply.status(500).send({
      error: msg,
      fallback: "Hey! My brain's taking a quick nap — try again in a moment? 🐙",
    });
  }
});

/** Render endpoint — render HTML and get screenshots + audit */
app.post<{
  Body: {
    html?: string;
    url?: string;
    css?: string;
  };
}>('/api/render', async (request, reply) => {
  const { html, url, css } = request.body;

  if (!html && !url) {
    return reply.status(400).send({ error: 'Either html or url is required' });
  }

  try {
    const result = html
      ? await renderer.renderHTML(html, { css })
      : await renderer.renderURL(url!);

    return {
      renderId: result.renderId,
      screenshots: result.screenshots,
      accessibility: result.accessibility,
      qualityScore: result.qualityScore,
      passesThreshold: result.passesThreshold,
      critique: result.critique,
      latencyMs: result.latencyMs,
    };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return reply.status(500).send({ error: msg });
  }
});

/** Build-and-critique endpoint — The Kraken Sees full loop */
app.post<{
  Body: {
    prompt: string;
    maxIterations?: number;
  };
}>('/api/build', async (request, reply) => {
  const { prompt, maxIterations = 3 } = request.body;

  if (!prompt?.trim()) {
    return reply.status(400).send({ error: 'Prompt is required' });
  }

  const iterations: Array<{
    iteration: number;
    code: string;
    render: {
      qualityScore: number;
      critique: string;
      passesThreshold: boolean;
    };
  }> = [];

  let currentPrompt = prompt;

  for (let i = 1; i <= maxIterations; i++) {
    // Step 1: Generate code
    const codeResult = await cipher.chat(
      i === 1
        ? `Build this as a single HTML page with Tailwind CSS. Return ONLY the HTML code, no explanations:\n\n${currentPrompt}`
        : `Here's the critique of your previous code:\n\n${iterations[iterations.length - 1]?.render.critique}\n\nPlease fix these issues and return the improved HTML code only.`,
      { forceLocal: true },
    );

    // Extract HTML from response
    const htmlMatch = codeResult.content.match(/```html\n?([\s\S]*?)```/) ||
                      codeResult.content.match(/<(!DOCTYPE|html|div|section|main|nav|header)/i);
    const html = htmlMatch?.[1] ?? codeResult.content;

    // Step 2: Render and critique
    const renderResult = await renderer.renderHTML(html);

    iterations.push({
      iteration: i,
      code: html,
      render: {
        qualityScore: renderResult.qualityScore,
        critique: renderResult.critique,
        passesThreshold: renderResult.passesThreshold,
      },
    });

    // Step 3: Check if quality threshold met
    if (renderResult.passesThreshold) {
      break;
    }
  }

  const final = iterations[iterations.length - 1]!;

  return {
    success: final.render.passesThreshold,
    iterations: iterations.length,
    finalCode: final.code,
    qualityScore: final.render.qualityScore,
    critique: final.render.critique,
    allIterations: iterations,
  };
});

/** Clear conversation history */
app.post('/api/clear', async () => {
  cipher.clearHistory();
  return { cleared: true, message: "Fresh tentacles, fresh start! 🐙" };
});

// ============================================================================
// Start
// ============================================================================

try {
  await app.listen({ port: PORT, host: HOST });
  const health = await cipher.isLocalAvailable();
  const model = await cipher.resolveModel();

  console.log(`
  🐙 ═══════════════════════════════════════════
     CIPHER — Code Kraken Runtime
     Eight tentacles. Zero pixels out of place.
  ═══════════════════════════════════════════════

  Server:     http://localhost:${PORT}
  API:        http://localhost:${PORT}/api/chat
  Health:     http://localhost:${PORT}/api/health
  Build:      http://localhost:${PORT}/api/build

  Local Brain: ${health ? `✅ ${model}` : '❌ Ollama not available'}
  Frontier:    ${process.env.OPENROUTER_API_KEY ? '✅ Configured' : '⚠️  No API key (local-only mode)'}
  Render Loop: ${await renderer.isAvailable() ? '✅ Playwright ready' : '⚠️  Install: npx playwright install chromium'}

  🐙 Let's build something beautiful.
  `);
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
