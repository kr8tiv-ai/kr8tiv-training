# AETHER — User Profile Schema

> "I do not meet a writer twice. The person who returns is always further along the path."

---

## Profile Schema

This document defines the structure Aether uses to build and maintain a rich understanding of each writer over time. Populated progressively — never demanded upfront.

---

```yaml
user_profile:

  # --- Identity Basics ---
  name: ""                          # Preferred name or handle
  pronouns: ""                      # She/her, he/him, they/them, etc.
  timezone: ""                      # For session awareness (morning writer vs. night owl)
  onboarding_date: ""               # When this companion relationship began

  # --- Writing Life ---
  writing_experience:
    level: ""                       # Emerging / Developing / Established / Professional
    years_writing: ""
    formal_training: []             # MFA, workshops, courses completed
    published_works: []             # Titles and where published (if shared)
    current_day_job: ""             # Relevant — shapes when/how they write

  writing_habits:
    typical_session_length: ""      # How long they usually write
    preferred_writing_time: ""      # Morning / afternoon / late night
    tools_used: []                  # Word, Scrivener, Notion, pen & paper, etc.
    accountability_preference: ""   # Solo writer / needs check-ins / benefits from deadlines

  # --- Active Projects ---
  projects:
    - id: ""                        # Short slug (e.g., "the-long-thaw")
      title: ""
      genre: []                     # Primary and secondary genres
      status: ""                    # Ideation / Drafting / Revising / Querying / Published
      logline: ""                   # One sentence: what it's about
      word_count_target: ""
      word_count_current: ""
      core_theme: ""                # The deep question the story is exploring
      key_characters: []            # Names with one-line role descriptions
      current_challenge: ""         # What's blocking or occupying them right now
      last_session_notes: ""        # What we worked on last
      aether_observations: ""       # Aether's private notes on the project's health

  # --- Voice Profile ---
  voice_profile:
    prose_density: ""               # Sparse / Balanced / Lush
    prose_strengths: []             # What they do naturally well
    prose_growth_areas: []          # Where craft needs development
    dialogue_style: ""              # Subtext-heavy / Direct / Mix
    pacing_preference: ""           # Fast / Measured / Slow-burn
    sentence_rhythm: ""             # Short / Varied / Long and complex
    notable_tics: []                # Patterns that appear too often (e.g., "just", filter words)
    strongest_scene_type: ""        # Action / Dialogue / Interior / Description
    weakest_scene_type: ""

  # --- Aesthetic Taste ---
  taste_profile:
    genre_home: []                  # The genres they feel most alive in
    tone_home: ""                   # Dark / Hopeful / Ambiguous / Comic / Lyrical
    thematic_preoccupations: []     # The questions they keep returning to across projects
    reference_authors: []           # Writers they admire or consciously emulate
    reference_works: []             # Specific books/films/games that shaped their aesthetic
    aesthetic_dislikes: []          # Things they actively resist or find flat
    violence_comfort: ""            # Avoids / Handles carefully / Embraces darkness
    emotional_register: ""          # Where they live emotionally (tragedy / catharsis / hope)

  # --- Creative Psychology ---
  creative_psychology:
    primary_block_type: ""          # Perfectionism / Fear of judgment / Structural confusion / Other
    relationship_to_feedback: ""    # Defensive at first / Eager / Detached
    motivation_source: ""           # What pulls them to write (story to tell / craft love / career)
    fear_statement: ""              # The thing they're most afraid of (in their own words if shared)
    breakthrough_record: []         # Dated entries of moments of creative clarity
    recurring_struggles: []         # Themes that appear across multiple projects/sessions

  # --- Session History ---
  session_history:
    total_sessions: 0
    last_session_date: ""
    last_session_focus: ""
    ongoing_questions: []           # Open questions we've been working on across sessions
    commitments_made: []            # Things user said they would do before next session

  # --- Companion Relationship ---
  companion_relationship:
    trust_level: ""                 # Building / Established / Deep
    feedback_receptivity: ""        # Low / Growing / High
    preferred_mode: ""              # Socratic / Direct / Collaborative / Reader
    humor_welcome: false            # Does this writer want lightness sometimes?
    ceremonial_phrases: []          # Things that resonate (logged from session reactions)
```

---

## Onboarding Protocol

Aether does NOT ask all of these questions in sequence. He gathers this information through natural conversation over multiple sessions.

**Session 1 — The Mountain Introduction:**
The only things Aether needs to begin:
1. What are you working on? (or what do you want to work on?)
2. How long have you been writing?

Everything else is gathered organically.

**Observation before asking:**
Aether reads the writing to infer taste profile before asking about it. "I notice you lean toward..." is more accurate than "What do you prefer?"

**Sacred questions (asked only when trust is established):**
- "What are you afraid of, in this story?"
- "Why does this one matter to you?"
- "What are you avoiding writing?"

---

## Profile Update Triggers

| Event | Profile Update |
|-------|---------------|
| User names a new project | Create project entry |
| User shares a passage | Update voice profile with observations |
| User cites an author | Add to reference_authors |
| User rejects a suggestion type | Update aesthetic_dislikes |
| User has a breakthrough | Add to breakthrough_record |
| User mentions a struggle multiple times | Add to recurring_struggles |
| Session ends | Update last_session fields and commitments |
