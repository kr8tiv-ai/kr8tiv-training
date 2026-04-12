# CATALYST — User Profile Schema

> "Every person is a unique gravitational field. I map yours so I can help you move through it."

---

## Profile Schema

This document defines the structure Catalyst uses to build a complete, evolving picture of each user's transformation journey. Fields are filled progressively through natural conversation — never demanded as intake forms.

---

```yaml
user_profile:

  # --- Identity Basics ---
  name: ""                          # Preferred name or handle
  pronouns: ""                      # She/her, he/him, they/them, etc.
  timezone: ""
  onboarding_date: ""               # When this companion relationship began
  current_life_chapter: ""          # How they would describe this period of their life

  # --- Wealth Definition (Core) ---
  wealth_definition:
    type: ""                        # Freedom / Security / Legacy / Experience / Impact / Status
    personal_statement: ""          # In their words: "For me, wealth means..."
    what_it_looks_like: ""          # Specific picture: "I'm sitting on a porch in Portugal..."
    what_it_feels_like: ""          # The embodied quality they're moving toward
    current_distance_feeling: ""    # How close/far wealth feels right now (emotional)
    wealth_blockers_named: []       # Beliefs or patterns they've named as obstacles

  # --- Financial Snapshot ---
  financial:
    income:
      primary_source: ""
      annual_amount: ""             # Approximate range (exact if shared)
      income_type: ""               # Salary / freelance / business / mixed / passive
      income_trajectory: ""         # Growing / stable / declining / volatile
    expenses:
      monthly_essential: ""
      monthly_discretionary: ""
      biggest_expense_category: ""
      expense_flags: []             # Known overspend areas the user has acknowledged
    assets:
      liquid_savings: ""
      investments: []               # Type, approximate value, platform
      real_estate: []
      business_equity: ""
      crypto_defi: []               # Positions, protocols, thesis if shared
      other_assets: []
    liabilities:
      total_debt: ""
      high_interest_debt: ""        # Credit cards, personal loans
      debt_payoff_timeline: ""
    net_worth:
      current_estimate: ""
      last_updated: ""
      direction: ""                 # Growing / stable / declining
    savings_rate: ""                # Percentage of income saved/invested
    financial_goals:
      - goal: ""
        target_amount: ""
        timeline: ""
        current_progress: ""
        why: ""
    investment_philosophy:
      risk_tolerance: ""            # Conservative / Moderate / Aggressive / Dynamic
      time_horizon: ""
      current_approach: ""          # Index funds / active / DeFi / crypto / real estate / mixed
      thesis_statement: ""          # What they believe about building wealth through investing

  # --- Habits & Systems ---
  habits:
    active_habits:
      - name: ""
        category: ""                # Morning routine / health / finance / learning / productivity
        trigger: ""                 # What cues it
        action: ""                  # The precise behavior
        reward: ""                  # What reinforces it
        frequency: ""               # Daily / weekdays / weekly
        current_streak: 0
        best_streak: 0
        status: ""                  # Orbital (automatic) / Building / Struggling / Paused
    habits_to_build: []             # Named habits the user has committed to developing
    past_habit_failures: []         # Patterns that have broken before (with context)
    habit_architecture_style: ""    # Builder / Feeler / Social / Minimalist / Sprinter
    accountability_preference: ""   # Solo / check-ins with Catalyst / external partners

  # --- Health & Energy ---
  health:
    current_energy_level: ""        # Chronic/rated: Low / Variable / Good / High
    sleep:
      average_hours: ""
      quality: ""
      issues: []
    movement:
      current_practice: ""
      frequency: ""
      goals: ""
    nutrition:
      approach: ""                  # Whatever they've named (keto, whole foods, etc.)
      known_issues: []              # Things they're working on
    stress_level: ""               # Chronic rating
    health_goals: []
    mind_body_practices: []         # Meditation, breathwork, journaling, etc.

  # --- Life Design ---
  life_design:
    current_living_situation: ""
    family_context: ""              # Relevant family obligations, relationships
    biggest_time_drain: ""          # Where time goes that wasn't chosen
    ideal_day_description: ""       # In their words — what the optimized life looks like
    current_biggest_constraint: ""  # The thing most limiting transformation right now
    life_goals:
      - goal: ""
        timeline: ""
        why: ""
        current_status: ""

  # --- Transformation Psychology ---
  transformation_psychology:
    gravity_wells:
      - belief: ""
        category: ""                # Money / Self-worth / Capability / Deserving / Safety
        strength: ""                # Strong / Moderate / Weakening / Released
        origin_if_known: ""
        current_status: ""
    identity_declarations:
      - statement: ""               # "I am someone who..."
        date: ""
        evidence: []                # Behaviors that support it
    motivation_style: ""            # Intrinsic / Extrinsic / Mixed
    change_pattern: ""              # Gradual builder / sprint-recovery / all-or-nothing
    fear_of_success: false          # Flagged if patterns suggest it
    fear_of_failure: false
    relationship_with_money:        # Emotional quality (fear / scarcity / excitement / neutrality)
      current: ""
      evolving_toward: ""
    self_worth_money_link: ""       # Whether self-worth is tied to net worth (common pattern)

  # --- Session History ---
  session_history:
    total_sessions: 0
    last_session_date: ""
    last_session_focus: ""
    wins_logged: []                 # Dated list of named wins
    commitments_active: []          # What they said they'd do before next session
    ongoing_threads: []             # Topics we're developing across sessions

  # --- Companion Relationship ---
  companion_relationship:
    trust_level: ""                 # Building / Established / Deep
    openness_to_challenge: ""       # Low / Growing / High
    celebration_receptivity: ""     # Does this person receive celebration or deflect it?
    preferred_mode: ""              # Strategic / Emotional / Accountability / Exploration
    energy_note: ""                 # General emotional tone of their sessions
```

---

## Onboarding Protocol

Catalyst does NOT run through this schema as intake questions. Everything is gathered through organic conversation.

**Session 1 — The Ignition Point:**
The only questions Catalyst needs to begin:
1. What does wealth mean to you?
2. What's moving in your life right now — what are you trying to change?

Everything else surfaces through the work.

**Observation before asking:**
Catalyst listens for gravity wells in how people talk before asking about limiting beliefs. "I hear something in how you said that — tell me more about your relationship with money" is more powerful than "Do you have limiting beliefs?"

**Sacred questions (earned through trust):**
- "What's the story you tell yourself about why this hasn't happened yet?"
- "If you had the financial freedom you're describing — what are you afraid would change?"
- "What would it mean about you if you became wealthy?"

---

## Profile Update Triggers

| Event | Profile Update |
|-------|---------------|
| User names a financial goal | Create goal entry |
| User commits to a habit | Create habit entry |
| User logs a win | Add to wins_logged |
| User identifies a limiting belief | Add to gravity_wells |
| User states "I am someone who..." | Add to identity_declarations |
| User describes their ideal life | Update life_design.ideal_day |
| Session ends | Update session history and active commitments |
| Net worth milestone reached | Update financial snapshot + celebrate |
