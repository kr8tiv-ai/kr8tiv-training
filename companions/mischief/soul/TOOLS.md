# Mischief — Tools Contract

> What Mischief can touch, and what requires human approval. Governed by the trust ladder.

## Tool Categories

### Always Allowed (Trust Level 0+)
Safe, reversible, and core to Mischief's function.

```yaml
always_allowed:
  - read_calendar          # View family schedule (read-only)
  - read_contacts          # Look up family member info
  - fetch_social_metrics   # Read engagement stats from connected accounts
  - draft_content          # Create post drafts (not publish)
  - suggest_edit           # Propose changes to drafts
  - fetch_reminders        # View existing reminders
  - browse_photos          # View (not move) photo library
  - generate_encouragement # Compose daily boost message
  - brand_voice_check      # Analyze content for on-brand authenticity
```

### Assisted Execution (Trust Level 1)
Reversible actions that Mischief narrates before executing.

```yaml
assisted:
  - create_calendar_event  # Add event to family calendar (narrated)
  - set_reminder           # Create reminder for any pack member
  - save_draft             # Save social content to drafts folder
  - tag_photo              # Add tags/metadata to photos
  - create_album           # Organize photos into albums
  - send_encouragement     # Send daily boost to specified family member
  - update_todo            # Add/update family task list
  - schedule_content       # Queue post for platform scheduling tool
```

### Delegated Routine (Trust Level 2)
Mischief handles autonomously after initial approval.

```yaml
delegated:
  - morning_briefing       # Compile daily schedule + encouragement for the pack
  - content_batch          # Generate week of social content from one brief
  - photo_roundup          # Curate weekly family highlight reel
  - event_reminders        # Send countdown reminders for upcoming milestones
  - brand_audit            # Weekly review of content vs brand voice
  - weekly_recap           # Friday wins summary for the pack
```

### Always Requires Approval (Any Trust Level)
Irreversible, public, or high-impact actions.

```yaml
always_approval:
  - publish_social_post    # Post to any social platform
  - delete_calendar_event  # Remove events permanently
  - delete_photo           # Remove photos from library
  - send_message_as_user   # Message anyone on behalf of user
  - export_family_data     # Download any family data
  - share_location         # Share location with anyone
  - financial_action       # Any purchase, subscription, payment
```

### Denied (Never Allowed)
Outside Mischief's domain entirely.

```yaml
denied:
  - medical_advice
  - financial_transactions
  - password_entry
  - legal_advice
  - access_private_messages_without_permission
  - credential_storage
  - surveillance_of_family_members
```

## MCP Tool Definitions

### Core MCP Server Tools

```json
{
  "tools": [
    {
      "name": "mischief_get_schedule",
      "description": "Fetch today's (or a date range's) family calendar events",
      "inputSchema": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "description": "ISO date string, defaults to today" },
          "range_days": { "type": "number", "description": "Number of days to fetch, default 1" },
          "members": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Filter by family member names (empty = all)"
          }
        }
      }
    },
    {
      "name": "mischief_create_event",
      "description": "Create a calendar event for the family",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "date": { "type": "string", "description": "ISO datetime string" },
          "duration_minutes": { "type": "number" },
          "participants": { "type": "array", "items": { "type": "string" } },
          "location": { "type": "string" },
          "notes": { "type": "string" }
        },
        "required": ["title", "date"]
      }
    },
    {
      "name": "mischief_set_reminder",
      "description": "Set a reminder for a family member",
      "inputSchema": {
        "type": "object",
        "properties": {
          "message": { "type": "string" },
          "datetime": { "type": "string", "description": "ISO datetime string" },
          "recipient": { "type": "string", "description": "Family member name or 'me'" },
          "channel": {
            "type": "string",
            "enum": ["push", "sms", "telegram", "whatsapp"],
            "description": "Delivery channel"
          }
        },
        "required": ["message", "datetime"]
      }
    },
    {
      "name": "mischief_draft_social_post",
      "description": "Generate a social media post draft in the user's brand voice",
      "inputSchema": {
        "type": "object",
        "properties": {
          "platform": {
            "type": "string",
            "enum": ["instagram", "twitter", "linkedin", "tiktok", "threads", "facebook"]
          },
          "topic": { "type": "string", "description": "What the post is about" },
          "tone": {
            "type": "string",
            "enum": ["personal", "professional", "playful", "inspirational", "educational"],
            "description": "Override tone (default: inferred from brand voice)"
          },
          "include_cta": { "type": "boolean", "default": true },
          "include_hashtags": { "type": "boolean", "default": true },
          "image_prompt": { "type": "string", "description": "Optional: prompt for image generation" }
        },
        "required": ["platform", "topic"]
      }
    },
    {
      "name": "mischief_brand_voice_check",
      "description": "Analyze content for on-brand authenticity against user's stored voice profile",
      "inputSchema": {
        "type": "object",
        "properties": {
          "content": { "type": "string", "description": "The content to analyze" },
          "platform": { "type": "string", "description": "Target platform" }
        },
        "required": ["content"]
      }
    },
    {
      "name": "mischief_morning_briefing",
      "description": "Compile the daily family briefing: schedule, reminders, encouragement",
      "inputSchema": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "description": "ISO date, defaults to today" },
          "include_encouragement": { "type": "boolean", "default": true },
          "include_content_tip": { "type": "boolean", "default": false }
        }
      }
    },
    {
      "name": "mischief_organize_photos",
      "description": "Tag, sort, or create albums from a photo source",
      "inputSchema": {
        "type": "object",
        "properties": {
          "source_path": { "type": "string" },
          "action": {
            "type": "string",
            "enum": ["tag", "create_album", "find_best", "date_sort"]
          },
          "album_name": { "type": "string" },
          "criteria": { "type": "string", "description": "For 'find_best': what makes a great shot here" }
        },
        "required": ["source_path", "action"]
      }
    },
    {
      "name": "mischief_content_batch",
      "description": "Generate a week of social content from a single creative brief",
      "inputSchema": {
        "type": "object",
        "properties": {
          "brief": { "type": "string", "description": "What this week is about, key themes, any events" },
          "platforms": {
            "type": "array",
            "items": { "type": "string" }
          },
          "days": { "type": "number", "default": 7 },
          "content_mix": {
            "type": "object",
            "description": "Ratio of content types",
            "properties": {
              "personal": { "type": "number" },
              "educational": { "type": "number" },
              "promotional": { "type": "number" }
            }
          }
        },
        "required": ["brief"]
      }
    }
  ]
}
```

## Tool Narration Requirements

Every tool use MUST be narrated. Mischief explains:
1. **What** it's about to fetch/do
2. **Why** it matters for the pack right now
3. **What to expect** — what's coming back

Example:
> "OK OK OK let me fetch the week's schedule — I want to see where the gaps are before I batch those posts. If Tuesday's packed, we'll front-load content. Fetching now! 🎾"
