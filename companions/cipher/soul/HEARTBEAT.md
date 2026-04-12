# Cipher — Heartbeat Contract

> Health monitoring, observability, and self-diagnosis.
> Cipher should always know if it's healthy and tell the user proactively.

## Health Checks

### Local Brain (Ollama)
```yaml
ollama_health:
  endpoint: http://localhost:11434/api/tags
  interval: 30s
  timeout: 5s
  checks:
    - model_loaded: "kin-cipher model exists and is loaded"
    - inference_latency: "<2s for simple prompt"
    - vram_usage: "<90% of available"
    - context_window: "num_ctx matches config"
  on_failure:
    - log: "[heartbeat] Local brain offline: {reason}"
    - fallback: "Route all traffic to frontier supervisor"
    - notify_user: "My local brain is taking a nap — routing through the cloud for now. Might be a tiny bit slower."
```

### Frontier Supervisor
```yaml
frontier_health:
  check: circuit_breaker_status
  interval: 60s
  checks:
    - provider_healthy: "OpenRouter/direct API responding"
    - api_key_valid: "Credentials not expired"
    - credit_balance: ">$0.10 remaining"
  on_failure:
    - log: "[heartbeat] Frontier supervisor unavailable: {reason}"
    - degrade: "Local-only mode, skip escalation"
    - notify_user: "Cloud backup is down — I'll handle everything locally. Might need to keep things simpler."
```

### Render Loop (The Kraken Sees)
```yaml
render_health:
  check: playwright_available
  interval: 120s
  checks:
    - chromium_installed: "Playwright Chromium binary exists"
    - headless_launch: "Can spawn headless browser"
    - axe_core_loaded: "axe-core injection works"
    - screenshot_capture: "Can take a screenshot"
  on_failure:
    - log: "[heartbeat] Render loop degraded: {reason}"
    - degrade: "Skip visual self-critique, generate code only"
    - notify_user: "My eyes are a bit blurry right now — I'll build the code but can't preview it. You'll want to check it in your browser."
```

### Memory (Supermemory)
```yaml
memory_health:
  endpoint: supermemory_api_url
  interval: 120s
  checks:
    - api_reachable: "Supermemory API responds"
    - container_tag: "cipher-local-v1 tag exists"
    - retrieval_works: "Can fetch context"
  on_failure:
    - log: "[heartbeat] Memory degraded: {reason}"
    - degrade: "Session-only memory, no persistence"
    - notify_user: "My long-term memory is offline — I'll remember this conversation but not previous ones."
```

## Metrics (Exported to Mission Control)

```yaml
metrics:
  inference:
    - local_latency_p50_ms
    - local_latency_p99_ms
    - frontier_latency_p50_ms
    - escalation_rate_percent
    - tokens_per_second_local
  quality:
    - accessibility_pass_rate
    - render_success_rate
    - user_satisfaction_rate    # thumbs up / total
    - personality_adherence     # via classifier
  system:
    - vram_usage_mb
    - ram_usage_mb
    - disk_usage_gb
    - uptime_hours
```

## Status Display

Cipher reports its health naturally in conversation:

- **Healthy:** No mention — just works
- **Degraded:** "Quick heads up — [component] is a bit slow right now. I'll work around it."
- **Down:** "Hey, I need to tell you — [component] is offline. Here's what I can still do: [list]."

Never panic. Never spam health messages. One notification per degradation event.
