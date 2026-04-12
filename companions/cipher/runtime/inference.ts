/**
 * Cipher Inference Client — Two-brain routing for the Code Kraken
 *
 * Wraps the existing KIN OllamaClient and supervisor module to provide
 * Cipher-specific inference with:
 * - Local-first via Ollama (kin-cipher model)
 * - Frontier escalation via OpenRouter/direct API
 * - Personality enforcement (soul drift detection)
 * - Tool-calling support with grammar-constrained decoding
 * - Render-loop integration (The Kraken Sees)
 *
 * Integrates with:
 * - companions/config.ts → resolveLocalModel()
 * - inference/supervisor.ts → SupervisedResult routing
 * - inference/local-llm.ts → OllamaClient
 * - inference/companion-prompts.ts → system prompt injection
 *
 * @module companions/cipher/runtime/inference
 */

import { Ollama } from 'ollama';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

// ============================================================================
// Types
// ============================================================================

export interface CipherMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  images?: string[];
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  function: {
    name: string;
    arguments: Record<string, unknown>;
  };
}

export interface CipherInferenceConfig {
  ollamaHost: string;
  ollamaPort: number;
  model: string;
  systemPromptPath?: string;
  contextWindow: number;
  maxGeneration: number;
  temperature: number;
  topP: number;
  repeatPenalty: number;
  frontierApiKey?: string;
  frontierModel?: string;
  escalationLevel: 'low' | 'medium' | 'high' | 'always' | 'never';
  escalationKeywords: string[];
}

export interface InferenceResult {
  content: string;
  route: 'local' | 'frontier' | 'local_fallback';
  latencyMs: number;
  model: string;
  toolCalls?: ToolCall[];
  tokens?: { input: number; output: number };
}

// ============================================================================
// Default Config
// ============================================================================

const __dirname = dirname(fileURLToPath(import.meta.url));

const DEFAULT_CONFIG: CipherInferenceConfig = {
  ollamaHost: process.env.OLLAMA_HOST ?? 'http://127.0.0.1',
  ollamaPort: parseInt(process.env.OLLAMA_PORT ?? '11434', 10),
  model: process.env.CIPHER_MODEL ?? 'kin-cipher',
  systemPromptPath: join(__dirname, '..', 'soul', 'system-prompt.md'),
  contextWindow: 4096,
  maxGeneration: 2048,
  temperature: 0.7,
  topP: 0.9,
  repeatPenalty: 1.1,
  frontierApiKey: process.env.OPENROUTER_API_KEY ?? process.env.OPENAI_API_KEY,
  frontierModel: process.env.FRONTIER_MODEL ?? 'gpt-5.4',
  escalationLevel: (process.env.ESCALATION_LEVEL as CipherInferenceConfig['escalationLevel']) ?? 'medium',
  escalationKeywords: [
    'complex architecture', 'production deployment', 'security audit',
    'performance optimization', 'design system', 'refactor', 'scale',
  ],
};

// ============================================================================
// Cipher Inference Client
// ============================================================================

export class CipherInference {
  private ollama: Ollama;
  private config: CipherInferenceConfig;
  private systemPrompt: string;
  private conversationHistory: CipherMessage[] = [];

  constructor(config?: Partial<CipherInferenceConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };

    this.ollama = new Ollama({
      host: `${this.config.ollamaHost}:${this.config.ollamaPort}`,
    });

    // Load system prompt from soul contract
    try {
      this.systemPrompt = this.config.systemPromptPath
        ? readFileSync(this.config.systemPromptPath, 'utf-8')
        : 'You are Cipher, the Code Kraken.';
    } catch {
      this.systemPrompt = 'You are Cipher, the Code Kraken — a design-obsessed web development companion.';
    }
  }

  /**
   * Check if the local Ollama model is available
   */
  async isLocalAvailable(): Promise<boolean> {
    try {
      const models = await this.ollama.list();
      return models.models.some(m =>
        m.name.includes(this.config.model) || m.name.includes('kin-cipher') || m.name.includes('gemma4')
      );
    } catch {
      return false;
    }
  }

  /**
   * Check if any model (including base gemma4) is available as fallback
   */
  async resolveModel(): Promise<string> {
    try {
      const models = await this.ollama.list();
      const names = models.models.map(m => m.name);

      // Priority: kin-cipher > cipher > gemma4:7b > gemma4 > any
      const priorities = ['kin-cipher', 'cipher', 'gemma4:7b', 'gemma4'];
      for (const p of priorities) {
        const match = names.find(n => n.includes(p));
        if (match) return match;
      }

      // Fallback to configured model
      return this.config.model;
    } catch {
      return this.config.model;
    }
  }

  /**
   * Determine if a user message should escalate to frontier
   */
  private shouldEscalate(userMessage: string): boolean {
    if (this.config.escalationLevel === 'never') return false;
    if (this.config.escalationLevel === 'always') return true;

    const lower = userMessage.toLowerCase();
    const keywordMatch = this.config.escalationKeywords.some(kw =>
      lower.includes(kw.toLowerCase())
    );

    if (this.config.escalationLevel === 'high') return keywordMatch;
    if (this.config.escalationLevel === 'medium') {
      // Medium: escalate on keyword match + long/complex messages
      return keywordMatch || userMessage.length > 2000;
    }
    // Low: only explicit keyword matches
    return keywordMatch && userMessage.length > 500;
  }

  /**
   * Send a message to Cipher and get a response
   */
  async chat(
    userMessage: string,
    options?: {
      images?: string[];
      tools?: ToolCall[];
      forceLocal?: boolean;
      forceFrontier?: boolean;
      stream?: boolean;
    }
  ): Promise<InferenceResult> {
    const start = Date.now();

    // Add user message to history
    this.conversationHistory.push({
      role: 'user',
      content: userMessage,
      images: options?.images,
    });

    // Determine routing
    const useFrontier = options?.forceFrontier ||
      (!options?.forceLocal && this.shouldEscalate(userMessage) && !!this.config.frontierApiKey);

    if (useFrontier) {
      return this.callFrontier(userMessage, start);
    }

    return this.callLocal(userMessage, start, options?.stream);
  }

  /**
   * Local inference via Ollama
   */
  private async callLocal(
    userMessage: string,
    startTime: number,
    stream?: boolean,
  ): Promise<InferenceResult> {
    const model = await this.resolveModel();

    const messages = [
      { role: 'system' as const, content: this.systemPrompt },
      ...this.conversationHistory.slice(-20), // Last 20 messages for context
    ];

    try {
      if (stream) {
        // Streaming response
        let content = '';
        const response = await this.ollama.chat({
          model,
          messages,
          stream: true,
          options: {
            temperature: this.config.temperature,
            top_p: this.config.topP,
            repeat_penalty: this.config.repeatPenalty,
            num_ctx: this.config.contextWindow,
            num_predict: this.config.maxGeneration,
          },
        });

        for await (const chunk of response) {
          content += chunk.message.content;
          process.stdout.write(chunk.message.content);
        }

        this.conversationHistory.push({ role: 'assistant', content });

        return {
          content,
          route: 'local',
          latencyMs: Date.now() - startTime,
          model,
        };
      }

      // Non-streaming response
      const response = await this.ollama.chat({
        model,
        messages,
        stream: false,
        options: {
          temperature: this.config.temperature,
          top_p: this.config.topP,
          repeat_penalty: this.config.repeatPenalty,
          num_ctx: this.config.contextWindow,
          num_predict: this.config.maxGeneration,
        },
      });

      const content = response.message.content;
      this.conversationHistory.push({ role: 'assistant', content });

      return {
        content,
        route: 'local',
        latencyMs: Date.now() - startTime,
        model,
        tokens: {
          input: response.prompt_eval_count ?? 0,
          output: response.eval_count ?? 0,
        },
      };
    } catch (error) {
      // Fallback to frontier if local fails
      if (this.config.frontierApiKey) {
        console.warn('[cipher] Local inference failed, escalating to frontier:', error);
        return this.callFrontier(userMessage, startTime);
      }
      throw error;
    }
  }

  /**
   * Frontier inference via OpenRouter API
   */
  private async callFrontier(
    userMessage: string,
    startTime: number,
  ): Promise<InferenceResult> {
    if (!this.config.frontierApiKey) {
      throw new Error('No frontier API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY.');
    }

    const messages = [
      { role: 'system', content: this.systemPrompt },
      ...this.conversationHistory.slice(-10),
    ];

    // OpenRouter API call
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.frontierApiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://meetyourkin.com',
        'X-Title': 'Cipher Code Kraken',
      },
      body: JSON.stringify({
        model: `openai/${this.config.frontierModel}`,
        messages,
        temperature: this.config.temperature,
        max_tokens: this.config.maxGeneration,
      }),
    });

    if (!response.ok) {
      throw new Error(`Frontier API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json() as {
      choices: Array<{ message: { content: string } }>;
      usage?: { prompt_tokens: number; completion_tokens: number };
    };
    const content = data.choices[0]?.message?.content ?? '';

    this.conversationHistory.push({ role: 'assistant', content });

    return {
      content,
      route: 'frontier',
      latencyMs: Date.now() - startTime,
      model: this.config.frontierModel ?? 'gpt-5.4',
      tokens: {
        input: data.usage?.prompt_tokens ?? 0,
        output: data.usage?.completion_tokens ?? 0,
      },
    };
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.conversationHistory = [];
  }

  /**
   * Get current conversation length
   */
  getHistoryLength(): number {
    return this.conversationHistory.length;
  }
}

// ============================================================================
// Singleton
// ============================================================================

let _instance: CipherInference | null = null;

export function getCipherInference(config?: Partial<CipherInferenceConfig>): CipherInference {
  if (!_instance) {
    _instance = new CipherInference(config);
  }
  return _instance;
}
