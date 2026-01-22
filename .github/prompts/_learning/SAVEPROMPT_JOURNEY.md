# `/savePrompt` Learning Journey

> Pre→Post research documentation for prompt engineering upcycling

---

## Pre-Learning State

### Initial Understanding
- `/savePrompt` was a black box command
- No knowledge of `.prompt.md` specification
- Unclear how `argument-hint` mapped to user input

### Raw Session Processing
- Created `saveprompt_algorithm.py` for batch archival
- Extracted 7 task patterns with malformed templates
- Used `{placeholder}` syntax (incorrect)

---

## Research Discoveries

### 1. `.prompt.md` Specification

```yaml
---
name: commandName        # → /commandName
description: Brief desc  # Picker dropdown
argument-hint: Hint      # Input placeholder
tools: [ 'edit', ... ]   # Permissions
mode: agent|ask|edit     # Execution mode
---

Instructions with {{argument}} placeholder.
```

### 2. `{{argument}}` Interpolation

```
/myCommand user types this here
           ↑
           Becomes {{argument}} in prompt body
```

**Before**: `Create {describe what}` - static text
**After**: `Create {{argument}}.` - user input interpolated

### 3. Mode Field Semantics

| Mode | Behavior |
|------|----------|
| `agent` | Autonomous execution with tools |
| `ask` | Q&A without direct actions |
| `edit` | Inline editing mode |

---

## Post-Learning Improvements

### Script Fixes (`saveprompt_algorithm.py`)

| Change | Impact |
|--------|--------|
| `{{argument}}` syntax | VS Code interpolation works |
| Added `mode` field | Enables agentic execution |
| Clean templates | No session noise in output |
| Default to `.github/prompts/` | Auto-discovery by VS Code |

### Prompt Quality Gates

1. ✅ Uses `{{argument}}` (not `{placeholder}`)
2. ✅ Has `mode: agent` or `mode: ask`
3. ✅ Concise body (under 50 lines)
4. ✅ Clear output expectations
5. ✅ Appropriate `tools` array

---

## Artifacts Produced

| File | Purpose | Status |
|------|---------|--------|
| `saveprompt_algorithm.py` | Batch processor | ✅ Fixed |
| `improvePrompt.prompt.md` | Meta-improvement tool | ✅ Created |
| `createComponent.prompt.md` | Generate code | ✅ Clean |
| `refactorCode.prompt.md` | Improve structure | ✅ Clean |
| `debugIssue.prompt.md` | Fix bugs | ✅ Clean |
| `generateTests.prompt.md` | Create tests | ✅ Clean |
| `documentCode.prompt.md` | Add docs | ✅ Clean |
| `explainCode.prompt.md` | Explain concepts | ✅ Clean |
| `analyzeCode.prompt.md` | Review code | ✅ Clean |

---

## Key Insight

> **Native `/savePrompt` = Recipe**  
> **Our `saveprompt_algorithm.py` = Batch Implementation**

They complement each other:
- Native: Real-time generalization from active conversation
- Ours: Archival + pattern extraction from exported sessions

---

## SSOT Cross-Reference

When `copilot-instructions.md` is loaded, prompts gain **afterglow**—SSOT patterns available without duplication:

| SSOT Pattern | Prompt Benefit |
|--------------|----------------|
| FA¹⁻⁵ Axioms | Structured reasoning without verbose instructions |
| DAFP (PBS/SHS) | Implicit altitude control (micro ↔ macro) |
| PRISM (ROGBIV) | Diagnostic frequency awareness |
| Axiom Registry | Invocation pattern context |

**Middle ground**: Prompts remain portable (work without SSOT) but gain depth when SSOT present.

---

## How `/savePrompt` Actually Works

**Source location**: `github.copilot-chat-*/assets/prompts/savePrompt.prompt.md`

It's just a `.prompt.md` file. No MCP, no HTTP, no special implementation.

```yaml
---
name: savePrompt
description: Generalize the current discussion into a reusable prompt...
tools: [ 'edit', 'search' ]
---
# Instructions that Copilot's LLM interprets
```

**Discovery mechanism**: VS Code auto-discovers `.prompt.md` files in:
- Extension's `assets/prompts/` (built-in commands)
- Workspace's `.github/prompts/` (custom commands)

**Execution**: LLM reads prompt → interprets instructions → attempts to follow them.

**Reality**: No guaranteed behavior. Prompts are soft guidance, not hard implementations.
