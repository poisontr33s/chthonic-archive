# `/savePrompt` Deep Research

> Reference documentation for the prompt library  
> **Location**: `.github/prompts/`

---

## 1. VS Code `.prompt.md` Specification

### Format

```yaml
---
name: commandName        # camelCase → invoked as /commandName
description: Brief desc  # ≤15 words, shown in picker
argument-hint: Hint      # Placeholder text after /command
tools:                   # Requested permissions
  - edit
  - ...
mode: agent|ask|edit     # Execution mode
---

Instructions with {{argument}} placeholder.
```

### Field Semantics

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Becomes `/name` command |
| `description` | Yes | Picker dropdown text |
| `argument-hint` | No | Input placeholder |
| `tools` | No | Tool permissions |
| `mode` | No | `agent` (autonomous), `ask` (Q&A), `edit` (inline) |

### `argument-hint` Behavior

```
/beautifySessionArchive C:\path\to\session.txt
                        ↑
                        User input → available as {{argument}}
```

---

## 2. Native vs Script Comparison

| Aspect | `/savePrompt` Native | `saveprompt_algorithm.py` |
|--------|---------------------|---------------------------|
| Input | Active conversation | Exported session files |
| Processing | AI generalization | Regex + patterns |
| Output | Single prompt | Archive + multiple prompts |
| Archival | None | Full preservation |

**Architecture**: Native = recipe, Script = batch implementation

---

## 3. Prompt Library Contents

| Command | Mode | Use Case |
|---------|------|----------|
| `/beautifySessionArchive` | agent | Session → archive + prompts |
| `/createComponent` | agent | Generate code |
| `/refactorCode` | agent | Improve structure |
| `/debugIssue` | agent | Fix bugs |
| `/generateTests` | agent | Create tests |
| `/documentCode` | agent | Add docs |
| `/explainCode` | ask | Explain concepts |
| `/analyzeCode` | ask | Review code |

---

## 4. Script Usage

```bash
# Archive mode (beautify)
uv run python scripts/saveprompt_algorithm.py session.txt

# Extract mode (generate prompts → .github/prompts/)
uv run python scripts/saveprompt_algorithm.py session.txt --extract-prompts

# Both modes
uv run python scripts/saveprompt_algorithm.py session.txt -e -o archive.md
```

---

## 5. Key Improvements Made

1. ✅ Added `mode: agent` to all action prompts
2. ✅ Used `{{argument}}` placeholder properly
3. ✅ Cleaned malformed context patterns
4. ✅ Consolidated to `.github/prompts/`
5. ✅ Updated script default output location
