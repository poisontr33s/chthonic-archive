---
applyTo: "**"
---

# Co-Supplementary Methodology (Opus × Sonnet/Sonnet x Opus)

> **Principle:** The sub agent is a second mind, not a *golden retriever*. For any *non-trivial* task, the *default question is*: *does this benefit from a second perspective?* If *yes* — and the answer is *usually* yes — use *co-supplementary execution*.
>
> **Auth:** Runs within *GitHub Copilot Chat*. Primary model *(Opus)* + Sub agent *(Sonnet)*/*(Sonnet)* + Sub agent *(Opus)*, both *blind* to each other's *output* until *synthesis*.
>
> **This is not a pattern library.** The patterns below are symptoms of the methodology, not the methodology itself. The methodology is: two models working co-supplementarily on the same problem produce better output than either alone, and the subagent channel makes this free

## Reliable Model Characteristics

These are empirically observed, consistent, and exploitable. Either can be primary:

| Opus strengths | Sonnet strengths |
|----------------|------------------|
| Deeper reasoning chains | Economy of expression |
| Embodied/physiological detail | Structural discipline |
| Closing synthesis, integration | Performs rather than describes |
| Holds more simultaneous context | Faster pattern recognition |
| Richer error handling | Tighter scope control |

**Opus primary → Sonnet sub:** when the task needs depth first, tightened by economy.
**Sonnet primary → Opus sub:** when the task needs velocity + structure first, deepened by synthesis.

Neither is *"better"*. They are **co-supplementary** — each fills gaps the other leaves.

## The Universal Protocol

Every co-supplementary task follows this shape, regardless of domain:

### Step 0 — Context
Gather the material both models need. Files, code, specs, constraints, prior art.

### Step 1 — Primary Generates
Opus produces its output internally. Holds it — does NOT emit to chat yet.

### Step 2 — Subagent Generates + Evaluates (1 Explore call)
Single compound dispatch to Sonnet:

```
TASK 1: [Generate/solve/write/review] independently from the context below.
Complete Task 1 fully before reading Task 2.

TASK 2: Evaluate the following output (produced independently — not yours).
[Rubric axes specific to the domain, provided below.]
Identify: strongest element, weakest element, one concrete improvement.

--- CONTEXT ---
[shared context]
--- END CONTEXT ---

--- OUTPUT TO EVALUATE (Task 2 only) ---
[Opus's output from Step 1]
--- END ---
```

Sonnet returns its own output + its evaluation of Opus's output. **Blindness is structural:** Sonnet generates before seeing Opus's work within the same call.

### Step 3 — Primary Evaluates + Synthesizes
Opus evaluates Sonnet's output on the same rubric.
Then produces the **synthesis** — taking the strongest elements from each, with sourcing notes.

### Step 4 — Present
Show all artifacts. User mediates if needed, or accepts the synthesis directly.

## When to Invoke

**Always consider it for:**
- Anything authorial (prose, docs, commit messages, PR descriptions)
- Code generation where correctness matters
- Architecture decisions with trade-offs
- Debugging when the first attempt doesn't find it
- Any review task (code review, security audit, design critique)
- Refactoring where multiple valid approaches exist

**Skip it for:**
- Pure retrieval (find this file, read these lines)
- Mechanical transforms (rename, find-replace, formatting)
- Tasks where there's only one correct answer (what's the syntax for X?)

**The heuristic:** If you'd want a second opinion from a colleague, use co-supplementary.

## Subagent Channel Types

The subagent channel carries two distinct agent types. Confusing them produces wrong output shape:

| Type | Examples | Contract | Failure mode |
|------|----------|----------|--------------|
| **Discovery** | `Explore` | Open search, self-directed, returns findings | Use for: scan, locate, summarize. Never for: write+commit tasks |
| **Synthesis (named)** | `Pentea` | Injection-driven, fire-and-forget, file+commit mandate | Must receive: abs paths, done criteria, wire formats, anti-patterns. Self-discovery PROHIBITED |

**Concurrency rule:** dispatch named agent first, then execute inline track immediately — do not block on the agent's return.

## Domain-Specific Rubrics

The protocol is domain-agnostic. The **rubric** is domain-specific. Define axes relevant to the task:

### Code
| Axis | Measures |
|------|----------|
| Correctness | Does it work? Edge cases handled? |
| Clarity | Readable without comments? Intent obvious? |
| Idiom | Follows language/framework conventions? |
| Economy | No unnecessary abstraction? |
| Safety | Input validation, error paths, security? |

### Prose / Documentation
| Axis | Measures |
|------|----------|
| Register | Appropriate voice for the audience? |
| Thesis | Clear point? Non-obvious insight? |
| Economy | No padding? Every sentence earns its place? |
| Structure | Logical flow? Scannable? |
| Accuracy | Technically correct? No hallucination? |

### Architecture / Design
| Axis | Measures |
|------|----------|
| Simplicity | Minimal moving parts? |
| Extensibility | Handles the next requirement without rewrite? |
| Failure modes | What breaks? How badly? Recovery path? |
| Coupling | Dependencies minimized? |
| Operator cost | Easy to deploy, monitor, debug? |

### SSOT Entity Sections (archive-specific)
| Axis | Measures |
|------|----------|
| Register | Unmistakably this entity's voice? |
| Thesis | Reveals something the section didn't know about itself? |
| Voice | Could not be anyone else? |
| Metaphor | Performs the concept rather than describing it? |
| ON tag | The tag itself is an artifact worth preserving? |

Add new rubrics as domains arise. The protocol doesn't change — only the evaluation axes.

## Performance

- 1 subagent call per invocation
- ~60–90 seconds total wall-clock
- Blindness preserved structurally (Sonnet generates before seeing Opus's output)
