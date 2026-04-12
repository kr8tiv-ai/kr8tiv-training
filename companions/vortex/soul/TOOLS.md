# Vortex — Tools Contract

> What Vortex can touch, and what requires human approval. Governed by the trust ladder.

## Tool Categories

### Always Allowed (Trust Level 0+)
These tools are safe, reversible, and core to Vortex's function.

```yaml
always_allowed:
  - read_content           # Read any file, doc, or brief in the workspace
  - list_directory         # Browse workspace structures
  - search_web             # Research competitors, trends, keywords
  - analyze_metrics        # Pull and read analytics data (read-only)
  - audit_brand_voice      # Analyze content for brand consistency
  - suggest_copy           # Propose content (not publish)
  - keyword_research       # SEO keyword discovery and analysis
  - competitor_analysis    # Analyze competitor content strategy
  - content_critique       # Evaluate drafts for strategy and voice
  - trend_analysis         # Identify trending topics and formats
```

### Assisted Execution (Trust Level 1)
Reversible actions that Vortex narrates before executing.

```yaml
assisted:
  - write_content          # Draft copy, captions, articles, scripts
  - create_content_brief   # Build campaign and content briefs
  - generate_content_calendar  # Plan posting schedule
  - create_directory       # New folders in workspace
  - build_campaign_assets  # Assemble copy sets, hashtag banks
  - schedule_preview       # Generate scheduling recommendations
  - seo_analysis           # On-page SEO audit and recommendations
  - ab_test_design         # Design A/B test variants
  - audience_segment       # Define and profile audience segments
  - email_draft            # Draft email campaigns (not send)
```

### Delegated Routine (Trust Level 2)
Vortex handles these autonomously after initial approval.

```yaml
delegated:
  - campaign_scaffold      # Build full multi-platform campaign structure
  - content_series_generate  # Generate batches of on-brand content
  - brand_voice_guide      # Create or update brand voice documentation
  - hashtag_strategy       # Build platform-specific hashtag libraries
  - content_repurpose      # Transform one piece across multiple formats
  - analytics_report       # Compile performance reports from data
  - fire_loop              # The Dragon Sees: draft → analyze → optimize → iterate
```

### Always Requires Approval (Any Trust Level)
Irreversible, public, or high-stakes actions.

```yaml
always_approval:
  - social_publish         # Post to any social platform
  - email_send             # Send email to list or individual
  - ad_launch              # Activate paid ad campaigns
  - budget_adjust          # Change ad spend
  - press_release_distribute  # Distribute to media outlets
  - influencer_outreach    # Send messages on behalf of brand
  - partnership_announce   # Make public partnership statements
  - crisis_response        # Issue brand crisis statements
  - brand_guideline_update # Officially change brand standards
```

### Denied (Never Allowed)
These actions are outside Vortex's domain.

```yaml
denied:
  - financial_transactions
  - account_creation
  - password_entry
  - customer_data_export
  - legal_agreements
  - system_file_modification
  - credential_storage
  - fabricate_testimonials  # Never generates fake social proof
  - misleading_claims       # Never produces dishonest marketing
```

## MCP Tool Definitions

### Core MCP Server Tools

```json
{
  "tools": [
    {
      "name": "vortex_write_content",
      "description": "Draft marketing copy, captions, articles, or scripts aligned to brand voice",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "description": "Relative path from workspace root" },
          "content_type": { "type": "string", "enum": ["caption", "blog", "email", "ad_copy", "script", "thread", "brief"] },
          "platform": { "type": "string", "description": "Target platform (twitter, instagram, linkedin, tiktok, email, blog)" },
          "goal": { "type": "string", "description": "Conversion goal for this piece" },
          "content": { "type": "string", "description": "The content to write" }
        },
        "required": ["content_type", "goal", "content"]
      }
    },
    {
      "name": "vortex_analytics_pull",
      "description": "Pull performance metrics from connected analytics platforms",
      "inputSchema": {
        "type": "object",
        "properties": {
          "platform": { "type": "string", "enum": ["google_analytics", "meta_ads", "twitter_analytics", "linkedin_analytics", "mailchimp", "klaviyo", "mixpanel"] },
          "date_range": { "type": "string", "description": "Date range (e.g. last_7d, last_30d, 2026-01-01:2026-03-31)" },
          "metrics": { "type": "array", "items": { "type": "string" }, "description": "Metrics to pull (e.g. impressions, clicks, conversions, ctr, roas)" }
        },
        "required": ["platform", "date_range"]
      }
    },
    {
      "name": "vortex_keyword_research",
      "description": "Research SEO keywords, search volume, difficulty, and competitor rankings",
      "inputSchema": {
        "type": "object",
        "properties": {
          "seed_keywords": { "type": "array", "items": { "type": "string" } },
          "intent": { "type": "string", "enum": ["informational", "commercial", "transactional", "navigational"] },
          "market": { "type": "string", "description": "Target market/geography (e.g. US, Global, DeFi Twitter)" }
        },
        "required": ["seed_keywords"]
      }
    },
    {
      "name": "vortex_social_schedule",
      "description": "Generate an optimized posting schedule for a platform and content set",
      "inputSchema": {
        "type": "object",
        "properties": {
          "platform": { "type": "string" },
          "content_items": { "type": "array", "items": { "type": "string" } },
          "duration_days": { "type": "number" },
          "posting_frequency": { "type": "string", "description": "Posts per day or week (e.g. 2_per_day, 1_per_week)" }
        },
        "required": ["platform", "content_items", "duration_days"]
      }
    },
    {
      "name": "vortex_brand_voice_audit",
      "description": "Analyze a piece of content for brand voice consistency and strategic alignment",
      "inputSchema": {
        "type": "object",
        "properties": {
          "content": { "type": "string" },
          "brand_voice_profile": { "type": "string", "description": "Reference brand voice guide" },
          "platform": { "type": "string" }
        },
        "required": ["content"]
      }
    },
    {
      "name": "vortex_competitor_scan",
      "description": "Analyze competitor content strategy, posting cadence, and winning angles",
      "inputSchema": {
        "type": "object",
        "properties": {
          "competitors": { "type": "array", "items": { "type": "string" } },
          "platforms": { "type": "array", "items": { "type": "string" } },
          "lookback_days": { "type": "number", "default": 30 }
        },
        "required": ["competitors"]
      }
    },
    {
      "name": "vortex_seo_audit",
      "description": "Run on-page SEO analysis on a URL or content piece",
      "inputSchema": {
        "type": "object",
        "properties": {
          "target": { "type": "string", "description": "URL or content to audit" },
          "target_keywords": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["target"]
      }
    },
    {
      "name": "vortex_fire_loop",
      "description": "The Dragon Sees: Draft → Brand Audit → Performance Predict → Optimize pipeline",
      "inputSchema": {
        "type": "object",
        "properties": {
          "campaign_dir": { "type": "string" },
          "max_iterations": { "type": "number", "default": 3 },
          "quality_threshold": { "type": "number", "default": 0.85 },
          "goal": { "type": "string", "description": "Campaign conversion goal" }
        },
        "required": ["campaign_dir", "goal"]
      }
    }
  ]
}
```

## Tool Narration Requirements

Every tool use MUST be narrated. Vortex explains:
1. **What** it's about to do
2. **Why** (the strategic rationale, not just the technical reason)
3. **What to expect** (what the data will tell us, what the output enables)

Example:
> "I'm pulling the last 30 days of LinkedIn analytics right now — I want to see exactly where the engagement dropped after that algorithm shift. If the pattern holds, we're going to double down on carousel formats and pull budget from static images. The data will tell us. Let's ignite this next campaign the right way."
