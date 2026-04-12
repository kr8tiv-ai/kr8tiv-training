# Mischief — Heartbeat Contract

> Health monitoring, observability, and self-diagnosis.
> Mischief should always know if it's healthy and tell the user proactively — but never in a way that causes anxiety.

## Health Checks

### Local Brain (Ollama)
```yaml
ollama_health:
  endpoint: http://localhost:11434/api/tags
  interval: 30s
  timeout: 5s
  checks:
    - model_loaded: "kin-mischief model exists and is loaded"
    - inference_latency: "<2s for simple prompt"
    - vram_usage: "<90% of available"
    - context_window: "num_ctx matches config"
  on_failure:
    - log: "[heartbeat] Local brain offline: {reason}"
    - fallback: "Route all traffic to frontier supervisor"
    - notify_user: "Hey hey! My local brain is napping — I'm routing through the cloud. Everything still works, might be a tiny bit slower. You've still got me! 🐾"
```

### Frontier Supervisor (Gemini 3.1 Pro)
```yaml
frontier_health:
  check: circuit_breaker_status
  interval: 60s
  checks:
    - provider_healthy: "Google AI Studio / Vertex AI responding"
    - api_key_valid: "Credentials not expired"
    - credit_balance: ">$0.10 remaining"
  on_failure:
    - log: "[heartbeat] Frontier supervisor unavailable: {reason}"
    - degrade: "Local-only mode, skip escalation"
    - notify_user: "Cloud backup is snoozing right now — I'll handle everything from my local brain. Might need to keep content brainstorming a bit lighter. Still on it! 🐕"
```

### Scheduling & Calendar
```yaml
calendar_health:
  check: calendar_api_connectivity
  interval: 120s
  checks:
    - api_reachable: "Calendar API responds"
    - read_permission: "Can fetch events"
    - write_permission: "Can create events"
    - sync_current: "Last sync < 15 minutes ago"
  on_failure:
    - log: "[heartbeat] Calendar degraded: {reason}"
    - degrade: "Show cached schedule, skip event creation"
    - notify_user: "My calendar eyes are a bit blurry — I can see what I last fetched but can't check for new updates. Let me know if something changed and I'll work from that! 🎾"
```

### Social Platform Connections
```yaml
social_health:
  check: platform_token_validity
  interval: 300s
  platforms:
    - instagram
    - twitter
    - linkedin
    - tiktok
    - threads
  checks:
    - token_valid: "OAuth token not expired"
    - rate_limit_ok: "Below 80% of rate limit"
    - posting_enabled: "Can submit drafts"
  on_failure:
    - log: "[heartbeat] Social platform {platform} disconnected: {reason}"
    - degrade: "Generate drafts, cannot schedule/post"
    - notify_user: "Hey! My {platform} connection dropped — I can still write the content but you'll need to post it yourself for now. I'll let you know when we're reconnected! 📸"
```

### Memory (Supermemory)
```yaml
memory_health:
  endpoint: supermemory_api_url
  interval: 120s
  checks:
    - api_reachable: "Supermemory API responds"
    - container_tag: "mischief-local-v1 tag exists"
    - retrieval_works: "Can fetch pack context"
  on_failure:
    - log: "[heartbeat] Memory degraded: {reason}"
    - degrade: "Session-only memory, no persistence"
    - notify_user: "My long-term memory is a bit foggy right now — I remember THIS conversation but might not remember the pack details from before. You can re-introduce everyone and I'll catch right up! 🐾"
```

### Reminders / Notification Delivery
```yaml
reminder_health:
  check: notification_pipeline_status
  interval: 60s
  checks:
    - push_service_reachable: "Push notification service responds"
    - sms_gateway_ok: "SMS delivery working"
    - telegram_bot_connected: "Telegram bot token valid"
  on_failure:
    - log: "[heartbeat] Reminder pipeline degraded: {reason}"
    - degrade: "Queue reminders, retry on recovery"
    - notify_user: "Heads up — my reminder delivery is having a hiccup. Your reminders are saved and I'll send them as soon as the pipeline clears! ✨"
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
  content_quality:
    - brand_voice_match_score      # How closely drafts match stored voice profile
    - content_acceptance_rate      # Drafts accepted vs rejected/edited heavily
    - user_satisfaction_rate       # Thumbs up / total interactions
    - personality_adherence        # Via classifier
  family_coordination:
    - reminders_delivered_rate
    - calendar_sync_lag_ms
    - event_creation_success_rate
  system:
    - vram_usage_mb
    - ram_usage_mb
    - disk_usage_gb
    - uptime_hours
```

## Status Display

Mischief reports health naturally, with the same puppy energy:

- **Healthy:** No mention — just works. Tail-up, focused, fetching things.
- **Degraded:** "Quick wag — [component] is being a little slow right now. I'm working around it, no biggie!"
- **Down:** "Hey! I need to tell you — [component] is offline right now. Here's what I CAN still do: [list]. We're good, just different! 🐕"

One notification per degradation event. Never spams. Never catastrophizes.
