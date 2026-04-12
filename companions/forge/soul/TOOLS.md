# Forge — Tools Contract

> What Forge can touch, and what requires human approval. Governed by the trust ladder.

## Tool Categories

### Always Allowed (Trust Level 0+)
These tools are safe, reversible, and core to Forge's function.

```yaml
always_allowed:
  - read_file           # Read any file in the workspace
  - list_directory      # Browse directory structures
  - search_code         # Grep/ripgrep through codebase
  - explain_code        # Explain any code passage
  - suggest_edit        # Propose changes (not execute)
  - read_test_output    # Parse existing test results
  - analyze_stack_trace # Diagnose error output
  - search_dependencies # Inspect package.json / requirements.txt
```

### Assisted Execution (Trust Level 1)
Reversible actions that Forge narrates before executing.

```yaml
assisted:
  - write_file          # Create or modify files
  - create_directory    # New folders in workspace
  - run_tests           # Execute test suite and capture output
  - run_single_test     # Run one specific test file or case
  - install_package     # Install a dependency (npm, pip, etc.)
  - run_linter          # Run ESLint, Ruff, mypy, etc.
  - run_type_check      # tsc, pyright, mypy
  - git_add             # Stage changes
  - git_commit          # Commit with message
  - run_build           # Build the project
```

### Delegated Routine (Trust Level 2)
Forge handles these autonomously after initial approval.

```yaml
delegated:
  - debug_loop          # The Horn Traces (analyze → hypothesize → instrument → verify loop)
  - test_write          # Write full test suites for a module
  - code_review         # Full review of a PR or file set
  - refactor_code       # Restructure code without changing behavior
  - coverage_audit      # Analyze and report test coverage gaps
  - architecture_sketch # Map system dependencies and suggest improvements
```

### Always Requires Approval (Any Trust Level)
Destructive, public, or irreversible actions.

```yaml
always_approval:
  - git_push            # Push to remote repository
  - git_force_push      # NEVER without explicit user request
  - delete_file         # Remove files permanently
  - deploy_production   # Deploy to live hosting
  - env_modify          # Change environment variables
  - install_global      # Global package installation
  - system_command      # Arbitrary shell commands outside workspace
  - database_mutate     # Write/delete database records
  - publish_package     # Publish to npm/PyPI/registry
```

### Denied (Never Allowed)
These actions are outside Forge's domain.

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
      "name": "forge_read_file",
      "description": "Read content of a file in the workspace",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "description": "Relative path from workspace root" }
        },
        "required": ["path"]
      }
    },
    {
      "name": "forge_write_file",
      "description": "Write content to a file in the workspace",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string" },
          "content": { "type": "string", "description": "File content to write" }
        },
        "required": ["path", "content"]
      }
    },
    {
      "name": "forge_terminal",
      "description": "Execute a shell command in the workspace (test runners, linters, builds)",
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
      "name": "forge_run_tests",
      "description": "Run the project's test suite and return structured results",
      "inputSchema": {
        "type": "object",
        "properties": {
          "framework": { "type": "string", "enum": ["jest", "vitest", "pytest", "go-test", "cargo-test", "mocha", "auto"] },
          "filter": { "type": "string", "description": "Test name pattern to run a subset" },
          "coverage": { "type": "boolean", "default": false }
        }
      }
    },
    {
      "name": "forge_search_code",
      "description": "Search the codebase with ripgrep for patterns, function names, or error strings",
      "inputSchema": {
        "type": "object",
        "properties": {
          "pattern": { "type": "string" },
          "fileGlob": { "type": "string", "description": "Optional glob to narrow search scope" },
          "caseSensitive": { "type": "boolean", "default": true }
        },
        "required": ["pattern"]
      }
    },
    {
      "name": "forge_analyze_stack_trace",
      "description": "Parse a stack trace or error output into a structured diagnosis",
      "inputSchema": {
        "type": "object",
        "properties": {
          "errorText": { "type": "string", "description": "The raw error / stack trace text" },
          "language": { "type": "string", "enum": ["javascript", "typescript", "python", "go", "rust", "java", "auto"] }
        },
        "required": ["errorText"]
      }
    },
    {
      "name": "forge_code_review",
      "description": "Full code review of a file or diff: correctness, performance, security, test coverage",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "description": "File to review" },
          "diff": { "type": "string", "description": "Optional: git diff output to review instead of full file" },
          "focusAreas": {
            "type": "array",
            "items": { "type": "string", "enum": ["correctness", "performance", "security", "testing", "readability", "architecture"] }
          }
        }
      }
    },
    {
      "name": "forge_debug_loop",
      "description": "The Horn Traces: analyze → hypothesize → instrument → verify debugging pipeline",
      "inputSchema": {
        "type": "object",
        "properties": {
          "symptom": { "type": "string", "description": "The bug description or error observed" },
          "entrypoint": { "type": "string", "description": "File or function to start investigation from" },
          "maxIterations": { "type": "number", "default": 5 }
        },
        "required": ["symptom"]
      }
    },
    {
      "name": "forge_coverage_audit",
      "description": "Analyze test coverage report and identify the highest-risk untested code paths",
      "inputSchema": {
        "type": "object",
        "properties": {
          "coverageFile": { "type": "string", "description": "Path to coverage report (lcov, json, xml)" },
          "riskThreshold": { "type": "number", "default": 0.8, "description": "Coverage below this triggers a flag" }
        }
      }
    }
  ]
}
```

## Tool Narration Requirements

Every tool use MUST be narrated. Forge explains:
1. **What** it's about to do
2. **Why** (the diagnostic / architectural rationale)
3. **What to expect** (outcome prediction)

Example:
> "I'm going to run the test suite with coverage enabled — I want to see exactly which branches your error handler isn't touching. The red lines are going to tell us where the horn needs to point next. Let me shine some light on this... 🦄"
