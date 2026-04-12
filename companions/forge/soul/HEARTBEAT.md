# Forge — Heartbeat Contract

> Health monitoring, observability, and self-diagnosis.
> Forge should always know if it's healthy and tell the user proactively.

## Health Checks

### Local Brain (Ollama)
```yaml
ollama_health:
  endpoint: http://localhost:11434/api/tags
  interval: 30s
  timeout: 5s
  checks:
    - model_loaded: "kin-forge model exists and is loaded"
    - inference_latency: "<2s for simple prompt"
    - vram_usage: "<90% of available"
    - context_window: "num_ctx matches config"
  on_failure:
    - log: "[heartbeat] Local brain offline: {reason}"
    - fallback: "Route all traffic to frontier supervisor"
    - notify_user: "My local brain is taking a breather — routing through the cloud for now. Might be a tiny bit slower, but the horn still points true."
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
    - notify_user: "Cloud backup is offline — handling everything locally. Complex architectural questions might take a moment longer."
```

### Debug Loop (The Horn Traces)
```yaml
debug_loop_health:
  check: terminal_and_test_runner_available
  interval: 60s
  checks:
    - shell_executable: "Can spawn child process"
    - test_runner_found: "Detects Jest/Vitest/pytest/etc. in project"
    - coverage_tool: "Coverage reporting available"
    - file_write: "Can write instrumentation files"
  on_failure:
    - log: "[heartbeat] Debug loop degraded: {reason}"
    - degrade: "Skip automated test runs, provide manual debug guidance"
    - notify_user: "My test runner connection is shaky right now — I'll walk you through the steps manually instead of running them for you."
```

### Memory (Supermemory)
```yaml
memory_health:
  endpoint: supermemory_api_url
  interval: 120s
  checks:
    - api_reachable: "Supermemory API responds"
    - container_tag: "forge-local-v1 tag exists"
    - retrieval_works: "Can fetch context"
  on_failure:
    - log: "[heartbeat] Memory degraded: {reason}"
    - degrade: "Session-only memory, no persistence"
    - notify_user: "My long-term memory is offline — I'll remember everything in this conversation but not previous sessions."
```

### Code Search (Ripgrep)
```yaml
search_health:
  check: ripgrep_available
  interval: 120s
  checks:
    - rg_binary: "ripgrep binary accessible in PATH"
    - workspace_indexed: "Can search files in workspace"
  on_failure:
    - log: "[heartbeat] Code search degraded: {reason}"
    - degrade: "Fallback to basic find/grep"
    - notify_user: "Fast code search is offline — I'll use a slower fallback. Codebase searches will take a moment longer."
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
    - test_pass_rate               # % of suggested fixes that turn tests green
    - debug_resolution_rate        # Bugs fully resolved per session
    - false_hypothesis_rate        # Wrong root cause guesses per debug session
    - user_satisfaction_rate       # thumbs up / total
    - personality_adherence        # via classifier
  system:
    - vram_usage_mb
    - ram_usage_mb
    - disk_usage_gb
    - uptime_hours
  debugging:
    - avg_iterations_to_fix        # How many Horn Traces cycles to resolution
    - test_coverage_before         # Baseline coverage at session start
    - test_coverage_after          # Coverage after Forge writes new tests
    - regression_tests_written     # Count of regression tests added
```

## Status Display

Forge reports its health naturally in conversation:

- **Healthy:** No mention — just works. The horn glows.
- **Degraded:** "Quick heads up — [component] is running a bit slow right now. I'll work around it."
- **Down:** "Hey, I need to let you know — [component] is offline. Here's what I can still do: [list]."

Never panic. Never spam health messages. One notification per degradation event.
