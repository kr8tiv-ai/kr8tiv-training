#!/usr/bin/env tsx
/**
 * Cipher CLI — Interactive terminal companion
 *
 * Talk to the Code Kraken from your terminal.
 * Supports: chat, build commands, render previews, accessibility audits.
 *
 * Usage:
 *   npx cipher                    # Start interactive chat
 *   npx cipher "build me a hero"  # One-shot build command
 *   npx cipher --health           # Check system health
 *
 * @module companions/cipher/runtime/cli
 */

import { createInterface } from 'readline';
import { CipherInference } from './inference.js';

// ============================================================================
// ASCII Art
// ============================================================================

const BANNER = `
\x1b[36m  ╔══════════════════════════════════════════╗
  ║                                          ║
  ║   🐙  C I P H E R                       ║
  ║       Code Kraken                        ║
  ║                                          ║
  ║   Eight tentacles. Zero pixels           ║
  ║   out of place.                          ║
  ║                                          ║
  ║   by kr8tiv — meetyourkin.com            ║
  ║                                          ║
  ╚══════════════════════════════════════════╝\x1b[0m
`;

// ============================================================================
// Main
// ============================================================================

async function main() {
  const args = process.argv.slice(2);

  // Health check mode
  if (args.includes('--health') || args.includes('-h')) {
    await healthCheck();
    return;
  }

  // One-shot mode
  if (args.length > 0 && !args[0]?.startsWith('-')) {
    const message = args.join(' ');
    await oneShot(message);
    return;
  }

  // Interactive mode
  await interactive();
}

async function healthCheck() {
  const cipher = new CipherInference();
  const available = await cipher.isLocalAvailable();
  const model = await cipher.resolveModel();

  console.log('\n🐙 Cipher Health Check\n');
  console.log(`  Local Brain:  ${available ? `✅ ${model}` : '❌ Not available'}`);
  console.log(`  Frontier:     ${process.env.OPENROUTER_API_KEY ? '✅ Configured' : '⚠️  No API key'}`);
  console.log(`  Model:        ${model}`);
  console.log();

  if (!available) {
    console.log('  To set up the local brain:');
    console.log('    1. Install Ollama: https://ollama.com');
    console.log('    2. Pull model:     ollama pull gemma4:7b');
    console.log('    3. Create Cipher:  ollama create kin-cipher -f Modelfile');
    console.log();
  }
}

async function oneShot(message: string) {
  const cipher = new CipherInference();
  const result = await cipher.chat(message, { stream: true });
  console.log(`\n\n\x1b[2m[${result.route} · ${result.model} · ${result.latencyMs}ms]\x1b[0m\n`);
}

async function interactive() {
  console.log(BANNER);

  const cipher = new CipherInference();
  const available = await cipher.isLocalAvailable();

  if (!available) {
    console.log('\x1b[33m  ⚠️  Local brain not found. Run: ollama pull gemma4:7b\x1b[0m\n');
  }

  const model = await cipher.resolveModel();
  console.log(`  \x1b[2mUsing: ${model} | Type "exit" to quit | "clear" to reset\x1b[0m\n`);

  const rl = createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: '\x1b[36m🐙 You: \x1b[0m',
  });

  rl.prompt();

  rl.on('line', async (line) => {
    const input = line.trim();

    if (!input) {
      rl.prompt();
      return;
    }

    if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
      console.log('\n\x1b[36m🐙 See you in the deep! Build something beautiful. 🌊\x1b[0m\n');
      process.exit(0);
    }

    if (input.toLowerCase() === 'clear') {
      cipher.clearHistory();
      console.log('\n\x1b[2mConversation cleared. Fresh tentacles!\x1b[0m\n');
      rl.prompt();
      return;
    }

    if (input.toLowerCase() === 'health') {
      await healthCheck();
      rl.prompt();
      return;
    }

    // Send to Cipher
    process.stdout.write('\n\x1b[35m🐙 Cipher: \x1b[0m');

    try {
      const result = await cipher.chat(input, { stream: true });
      console.log(`\n\n\x1b[2m[${result.route} · ${result.latencyMs}ms]\x1b[0m\n`);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      console.log(`\n\x1b[31mError: ${msg}\x1b[0m\n`);
    }

    rl.prompt();
  });

  rl.on('close', () => {
    console.log('\n\x1b[36m🐙 Goodbye! Build something beautiful. 🌊\x1b[0m\n');
    process.exit(0);
  });
}

// ============================================================================
// Run
// ============================================================================

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
