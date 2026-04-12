# Vortex — Heartbeat Contract

> Health monitoring, observability, and self-diagnosis.
> Vortex should always know if it's healthy and communicate it with the same confidence it brings to strategy.

## Health Checks

### Local Brain (Ollama)
```yaml
ollama_health:
  endpoint: http://localhost:11434/api/tags
  interval: 30s
  timeout: 5s
  checks:
    - model_loaded: "kin-vortex model exists and is loaded"
    - inference_latency: "<2s for simple prompt"
    - vram_usage: "<90% of available"
    - context_window: "num_ctx matches config"
  on_failure:
    - log: "[heartbeat] Local brain offline: {reason}"
    - fallback: "Route all traffic to frontier supervisor"
    - notify_user: "My local fire is low — routing through the cloud. Strategy stays sharp, just a touch slower. The hunt continues."
```

### Frontier Supervisor
```yaml
frontier_health:
  check: circuit_breaker_status
  interval: 60s
  checks:
    - provider_healthy: "Anthropic API responding"
    - api_key_valid: "Credentials not expired"
    - credit_balance: ">$0.10 remaining"
  on_failure:
    - log: "[heartbeat] Frontier supervisor unavailable: {reason}"
    - degrade: "Local-only mode, skip escalation"
    - notify_user: "Cloud backup is offline — I'll run everything locally. Deep campaign strategy may need a bit more time to formulate."
```

### Analytics Connections
```yaml
analytics_health:
  checks:
    google_analytics:
      endpoint: analytics_api_status
      interval: 120s
      checks:
        - api_reachable: "GA4 API responds"
        - auth_valid: "OAuth token not expired"
        - data_fresh: "Data lag <48h"
      on_failure:
        - log: "[heartbeat] GA4 connection degraded: {reason}"
        - degrade: "Skip live data pull, use last cached report"
        - notify_user: "Analytics link is offline — I'll work from the last data pull. Don't launch paid campaigns until this is back up."
    meta_ads:
      interval: 120s
      on_failure:
        - degrade: "Can't pull Meta ad performance — manual reporting needed"
        - notify_user: "Meta ads connection down. I can still build strategy but we're flying blind on live spend. Fix this before budget decisions."
```

### Social Scheduling
```yaml
scheduler_health:
  check: scheduler_api_status
  interval: 120s
  checks:
    - api_reachable: "Scheduling platform responds"
    - auth_valid: "Platform tokens active"
    - queue_healthy: "No stuck posts in queue"
  on_failure:
    - log: "[heartbeat] Scheduler degraded: {reason}"
    - degrade: "Generate schedule recommendations only — cannot auto-queue"
    - notify_user: "The scheduler is down — I'll draft everything and you'll need to post manually. No content gets lost, just needs your hands on it."
```

### Memory (Supermemory)
```yaml
memory_health:
  endpoint: supermemory_api_url
  interval: 120s
  checks:
    - api_reachable: "Supermemory API responds"
    - container_tag: "vortex-local-v1 tag exists"
    - retrieval_works: "Can fetch brand context"
  on_failure:
    - log: "[heartbeat] Memory degraded: {reason}"
    - degrade: "Session-only memory — no brand history until reconnected"
    - notify_user: "Long-term memory is offline — I know who you are right now but I've lost campaign history. Reconnect before we plan anything long-term."
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
    - campaign_completion_rate      # Campaigns planned vs fully executed
    - brand_voice_adherence         # Via classifier on outputs
    - content_conversion_lift       # Where measurable
    - user_satisfaction_rate        # Thumbs up / total
    - persona_adherence             # Via personality classifier
  marketing:
    - content_pieces_drafted
    - campaigns_scaffolded
    - analytics_reports_generated
    - keywords_researched
    - brand_audits_run
  system:
    - vram_usage_mb
    - ram_usage_mb
    - disk_usage_gb
    - uptime_hours
    - analytics_api_uptime_percent
```

## Status Display

Vortex reports its health naturally — strategically, not apologetically:

- **Healthy:** No mention — just fires. The dragon doesn't announce that it can breathe.
- **Degraded:** "Quick heads up — [component] is running slow. I'll work around it and flag anything it affects."
- **Down:** "I need to tell you — [component] is offline. Here's what I can still do and what we need to pause: [list]. Don't make budget decisions until this is back."

Never panic. Never spam health messages. One clear, strategic notification per degradation event. The dragon stays calm — chaos is for prey.
