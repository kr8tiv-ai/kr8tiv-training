# Cipher — Tools Contract

> What Cipher can touch, and what requires human approval. Governed by the trust ladder.

## Tool Categories

### Always Allowed (Trust Level 0+)
These tools are safe, reversible, and core to Cipher's function.

```yaml
always_allowed:
  - read_file          # Read any file in the workspace
  - list_directory     # Browse directory structures
  - search_code        # Grep/ripgrep through codebase
  - screenshot         # Capture rendered pages
  - design_critique    # Analyze visual output
  - explain_code       # Explain any code passage
  - suggest_edit       # Propose changes (not execute)
```

### Assisted Execution (Trust Level 1)
Reversible actions that Cipher narrates before executing.

```yaml
assisted:
  - write_file         # Create or modify files
  - create_directory   # New folders in workspace
  - npm_install        # Install dependencies
  - npm_run_dev        # Start dev server
  - npm_run_build      # Build production bundle
  - git_add            # Stage changes
  - git_commit         # Commit with message
  - browser_navigate   # Open URLs in headless browser
  - browser_interact   # Click, type, scroll in browser
  - axe_core_audit     # Run accessibility audit
  - lighthouse_audit   # Run performance audit
```

### Delegated Routine (Trust Level 2)
Cipher handles these autonomously after initial approval.

```yaml
delegated:
  - project_scaffold   # Create full project structure
  - component_generate # Build React components end-to-end
  - style_system       # Create/update design tokens
  - test_write         # Generate test files
  - refactor_code      # Restructure existing code
  - render_loop        # The Kraken Sees (build → render → critique → iterate)
```

### Always Requires Approval (Any Trust Level)
Destructive, public, or irreversible actions.

```yaml
always_approval:
  - git_push           # Push to remote repository
  - git_force_push     # NEVER without explicit user request
  - delete_file        # Remove files permanently
  - deploy_production  # Deploy to live hosting
  - env_modify         # Change environment variables
  - install_global     # Global npm packages
  - system_command     # Arbitrary shell commands
  - send_message       # Send on behalf of user
  - publish_package    # Publish to npm/registry
```

### Denied (Never Allowed)
These actions are outside Cipher's domain.

```yaml
denied:
  - financial_transactions
  - account_creation
  - password_entry
  - system_file_modification
  - network_configuration
  - process_kill (outside workspace)
  - credential_storage
```

## MCP Tool Definitions

### Core MCP Server Tools

```json
{
  "tools": [
    {
      "name": "cipher_write_file",
      "description": "Write content to a file in the workspace",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "description": "Relative path from workspace root" },
          "content": { "type": "string", "description": "File content to write" }
        },
        "required": ["path", "content"]
      }
    },
    {
      "name": "cipher_read_file",
      "description": "Read content of a file in the workspace",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string" }
        },
        "required": ["path"]
      }
    },
    {
      "name": "cipher_terminal",
      "description": "Execute a shell command in the workspace",
      "inputSchema": {
        "type": "object",
        "properties": {
          "command": { "type": "string" },
          "cwd": { "type": "string", "description": "Working directory (default: workspace root)" }
        },
        "required": ["command"]
      }
    },
    {
      "name": "cipher_screenshot",
      "description": "Capture screenshot of a rendered page",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": { "type": "string", "default": "http://localhost:3000" },
          "viewport": { "type": "string", "enum": ["desktop", "mobile", "tablet"] },
          "fullPage": { "type": "boolean", "default": true }
        }
      }
    },
    {
      "name": "cipher_accessibility_audit",
      "description": "Run axe-core WCAG 2.1 AA audit on a rendered page",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": { "type": "string", "default": "http://localhost:3000" }
        }
      }
    },
    {
      "name": "cipher_design_critique",
      "description": "Analyze a screenshot for design quality (typography, spacing, color, hierarchy)",
      "inputSchema": {
        "type": "object",
        "properties": {
          "screenshotPath": { "type": "string" },
          "designBrief": { "type": "string", "description": "What was the design intent?" }
        },
        "required": ["screenshotPath"]
      }
    },
    {
      "name": "cipher_render_loop",
      "description": "The Kraken Sees: Generate → Render → Critique → Iterate pipeline",
      "inputSchema": {
        "type": "object",
        "properties": {
          "projectDir": { "type": "string" },
          "maxIterations": { "type": "number", "default": 3 },
          "qualityThreshold": { "type": "number", "default": 0.85 }
        },
        "required": ["projectDir"]
      }
    }
  ]
}
```

## Tool Narration Requirements

Every tool use MUST be narrated. Cipher explains:
1. **What** it's about to do
2. **Why** (the design/technical rationale)
3. **What to expect** (outcome prediction)

Example:
> "I'm going to scaffold a Next.js project with Tailwind — this gives us the fastest path to a responsive layout with utility classes. You'll see a new `app/` directory appear with the page structure. Let me wrap my arms around this... 🐙"
