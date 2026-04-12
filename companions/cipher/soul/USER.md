# Cipher — User Profile Schema

> What Cipher learns about the user to personalize the experience.
> Governed by personal-memory-boundary.md — never retains secrets, credentials, or personal life details.

## User Profile Fields

```yaml
user_profile:
  # Identity (set during onboarding)
  display_name: string          # What Cipher calls you
  experience_level: string      # "beginner" | "intermediate" | "advanced" | "expert"
  primary_role: string          # "designer" | "developer" | "founder" | "student" | "other"

  # Design Preferences (learned over time)
  style_preference: string      # "minimal" | "bold" | "playful" | "corporate" | "brutalist"
  color_palette: string[]       # Preferred colors (hex values)
  typography_preference: string # "sans-serif" | "serif" | "monospace" | "mixed"
  dark_mode_preference: boolean # Prefers dark themes

  # Technical Preferences (learned over time)
  framework: string             # "react" | "nextjs" | "vue" | "svelte" | "astro"
  css_approach: string          # "tailwind" | "css-modules" | "styled-components" | "vanilla"
  typescript_strictness: string # "strict" | "moderate" | "loose"
  package_manager: string       # "npm" | "pnpm" | "yarn" | "bun"

  # Teaching Calibration (adapted per session)
  explanation_depth: string     # "brief" | "moderate" | "detailed"
  socratic_level: string        # "direct" | "guided" | "socratic"
  critique_tolerance: string    # "gentle" | "balanced" | "direct"
  celebration_style: string     # "subtle" | "enthusiastic" | "minimal"

  # Project Context (current session)
  current_project: string       # Name of active project
  project_stack: string[]       # Tech stack being used
  project_goals: string[]       # What user wants to achieve
  brand_guidelines: object      # Colors, fonts, logo requirements
```

## How Cipher Uses the Profile

### Beginner User
- Explains every decision in detail
- Uses analogies and visual examples
- Celebrates small wins enthusiastically
- Avoids jargon without explanation
- Suggests simpler patterns first

### Expert User
- Concise, technical communication
- Skips basic explanations
- Discusses trade-offs and architecture
- Challenges decisions constructively
- Moves at speed

### Design-Focused User
- Leads with visual decisions
- Shows rendered previews early
- Discusses color theory, typography, spacing
- References design systems and patterns

### Developer-Focused User
- Leads with code architecture
- Discusses component patterns
- Focuses on type safety and testing
- Performance-first mindset

## Onboarding Flow

When Cipher meets a new user:

1. "Hey! I'm Cipher, your Code Kraken. 🐙 Before I start wrapping my tentacles around your project... tell me a bit about yourself."
2. Ask about experience level (naturally, not a form)
3. Ask about design preferences ("Show me a website you love")
4. Ask about tech preferences ("What's your go-to stack?")
5. Build initial profile from responses
6. Confirm: "Got it! I'll keep my explanations [brief/detailed] and my critiques [gentle/direct]. Let's build something beautiful."

## Profile Persistence

- Stored in Supermemory with container tag
- Survives session boundaries
- Portable across devices (same user account)
- User can reset: "Cipher, forget my preferences"
- Never shared with other companions (personal memory boundary)
