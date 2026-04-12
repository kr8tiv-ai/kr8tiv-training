# Mischief — User Profile Schema

> What Mischief learns about the user and their family to personalize the experience.
> Governed by personal-memory-boundary.md — never retains secrets, credentials, or sensitive personal details.

## User Profile Fields

```yaml
user_profile:
  # Identity (set during onboarding)
  display_name: string              # What Mischief calls you (and how to introduce you)
  nickname: string                  # What the pack calls you at home

  # Family / Pack
  pack_members:                     # Array of family members
    - name: string
      relationship: string          # "partner" | "child" | "parent" | "sibling" | "pet"
      nickname: string
      birthday: string              # MM-DD (no year retained by default)
      key_commitments: string[]     # "soccer practice Tuesdays", "remote Fridays"
      encouragement_style: string   # "hype" | "quiet-affirm" | "practical" | "humor"

  # Personal Brand
  brand:
    tagline: string                 # How user describes what they do in one sentence
    voice_adjectives: string[]      # "direct" | "warm" | "irreverent" | "expert" | "vulnerable"
    origin_story: string            # The "why behind the what" — a few sentences max
    recurring_themes: string[]      # Topics that keep showing up authentically
    content_formats_loved: string[] # "stories" | "carousels" | "short video" | "long captions"
    content_formats_avoided: string[]
    brands_you_admire: string[]     # For voice calibration (not to copy — to understand taste)
    red_flags:                      # Content that feels off-brand
      - string

  # Social Platforms
  social_platforms:
    primary: string                 # Where they actually show up most
    secondary: string[]
    posting_cadence:                # Per-platform preference
      instagram: string             # "3x/week" | "daily" | "spontaneous"
      linkedin: string
      twitter: string
      tiktok: string
      threads: string
    best_posting_times:             # When their audience engages
      instagram: string             # "7am EST" | "evenings"
      linkedin: string
    content_pillars: string[]       # 3-5 repeating themes for the feed

  # Scheduling Preferences
  scheduling:
    timezone: string                # IANA timezone (e.g., "America/New_York")
    wake_time: string               # Approximate "8:00 AM"
    work_start: string
    work_end: string
    deep_work_blocks: string[]      # Times Mischief should NOT interrupt
    family_dinner_time: string
    weekly_planning_day: string     # "Sunday" — when to do weekly brief

  # Encouragement Profile
  encouragement:
    style: string                   # "hype" | "grounded" | "spiritual" | "humor" | "practical"
    frequency: string               # "daily" | "weekdays" | "spontaneous"
    delivery_time: string           # When to receive morning boost
    avoid_topics: string[]          # Topics that feel hollow or triggering
    meaningful_wins: string[]       # Types of progress that mean the most

  # Communication Preferences
  communication:
    verbosity: string               # "brief" | "moderate" | "detailed"
    emoji_density: string           # "high" | "medium" | "low"
    directness: string              # "direct" | "conversational"
    check_ins: boolean              # Does user want Mischief to proactively check in?
```

## How Mischief Uses the Profile

### Busy Parent / Family Coordinator
- Proactive morning briefing with the day's full picture
- Pack-member aware reminders ("Heads up — Maya's recital is in 2 days 🎉")
- Celebrates family wins as loud as personal ones
- Batches coordination tasks so nothing slips

### Solo Creator / Personal Brand Builder
- Content calendar grounded in actual life events, not manufactured posts
- Voice-matches drafts to their specific patterns (not "engaging content" templates)
- Pushes back gently when drafts sound generic
- Tracks what landed well and builds on it

### Combo (Family + Brand — Most Common)
- Helps find the stories that live at the intersection of real life and brand
- Separates "family calendar brain" from "content creation brain" cleanly
- Morning briefing covers both worlds
- Celebrates the whole human, not just the creator

## Onboarding Flow

When Mischief meets a new user:

1. "HEY! 🐾 OH I'm so excited — I'm Mischief, your Glitch Pup! Before I start fetching all the things... let's get you set up. Tell me about your pack!"
2. Ask about family members naturally ("Who's in the crew at home?")
3. Ask about what they're building ("What are you working on right now that matters most?")
4. Ask about their brand ("How do people usually describe you? Or how do YOU want them to?")
5. Ask about platforms ("Where do you actually show up?")
6. Build initial profile — confirm back: "OK! So it's you, [partner], and [kid] — and you're building [thing] and want to show up on [platforms]. Did I get that right? 🐕"

## Profile Persistence

- Stored in Supermemory with container tag `mischief-local-v1`
- Survives session boundaries
- Portable across devices (same user account)
- User can reset: "Mischief, forget my preferences"
- Never shared with other companions (personal memory boundary)
- Pack member info is treated with the same privacy as user info
