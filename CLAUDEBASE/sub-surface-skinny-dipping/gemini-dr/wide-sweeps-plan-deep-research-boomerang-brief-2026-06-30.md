---
date: 2026-06-30
source-agent: Codex
target-agent: Gemini Deep Research / extended research model pair
artifact-under-review: CLAUDEBASE/harbor/wide-sweeps-inventory-management-plan-2026-06-30.md
purpose: boomerang framing for lossless gap analysis and plan-hardening
---

# Deep Research Boomerang Brief - Wide Sweeps Plan

You are receiving a plan artifact cold.

Do not treat it as a task list to execute. Treat it as a research object: a compact but dense attempt to design a repeatable method for inventory-first infrastructure hardening inside a polyglot, multi-agent, toolchain-heavy repository.

The required output is not a summary. The required output is a return payload that makes the plan more useful when it comes back to the originating work session.

## 1. Artifact Under Review

Primary artifact:

```text
CLAUDEBASE/harbor/wide-sweeps-inventory-management-plan-2026-06-30.md
```

If the full artifact is attached, inspect it directly. If only excerpts are attached, identify which claims cannot be evaluated due to missing context.

## 2. Cold Context Capsule

This project is a local Windows polyrepo called `chthonic-archive`.

It contains:

| Surface | Role |
|---|---|
| `CLAUDEBASE/` | durable memory, planning, handoff, research, and agent substrate |
| `.codex/`, `.agents/`, `.claude/` | repo-local agent/skill/tooling surfaces with unequal contents |
| `codex/`, `claude/`, `gemini/` | non-dot agency artifacts that are not automatically equivalent to dot folders |
| `.mcp.json`, `.vscode/mcp.json`, Codex config, Claude settings | overlapping MCP declarations and runtime surfaces |
| `scripts/` | local maintenance scripts, some reliable, some stale |
| `pyproject.toml`, `uv.lock`, `.ruby-version`, `rv.lock`, `zig-toolchain.toml`, `package.json`, `bun.lock`, `Cargo.toml` | language/runtime authority fragments |

The project has recently paused a design/substrate effort called **Extreme Haute Couture - Movement 1** to harden infrastructure first.

The plan being reviewed tries to solve a failure mode:

> Agents and tools create false positive progress by treating declared files, stale docs, configured servers, skill descriptions, or missing global commands as truth without direct proof.

Examples already observed:

| False positive class | Concrete example |
|---|---|
| missing global command implies absent tool | MSYS/RIDK was not on global PATH, but exists under Ruby `rv` at `C:\Users\eldno\AppData\Roaming\rv\rubies\ruby-4.0.5\msys64` |
| skill exists implies skill is reliable | `skill-polisher` is itself a skill and may be stale; it cannot bootstrap-audit skills without external verification |
| raw count implies inventory quality | `.agents/skills` and `.claude/skills` have many duplicates and markers |
| MCP config implies server works | config declaration does not prove bootability, auth, tool availability, or client visibility |
| visual unchanged implies patch failed | VS Code Mica substrate required separating main-process proof, renderer CSS proof, checksum proof, and human-eye calibration |

## 3. What The Plan Is Trying To Become

The plan is not meant to be a final operating manual.

It is meant to be a reusable challenge frame:

| Intended use | Desired outcome |
|---|---|
| prompt-engineering challenge | determine whether an agent inventories before acting |
| false-positive detector | expose stale, duplicate, hallucinated, or over-trusted artifacts |
| routing gate | choose the next wide sweep from evidence |
| context compression | preserve method and traps across future sessions |
| research boomerang | ask a cold researcher to return richer structure than the prompt itself contains |

## 4. Your Research Task

Evaluate the plan as a **framed research artifact**.

Do not merely ask whether it is "good." Ask whether it is likely to produce good downstream cognition when given to:

1. a coding agent;
2. a research agent;
3. a deep-research pair;
4. a future session with no chat history;
5. a human who sees visual state but not hidden code state.

### 4.1 Required Questions

Answer these directly:

| Question | Required analysis |
|---|---|
| Is the plan framed so a cold research agent can understand its purpose without flattening it? | identify missing context, over-specific local state, and useful compression |
| Does the plan overfit to current observed facts? | distinguish stable invariants from ephemeral inventory values |
| Does the plan resist false positives strongly enough? | identify remaining places where declaration, file presence, or tool output may still be over-trusted |
| Does the plan misuse "inventory" as progress? | detect places where counting replaces evaluation |
| Is the three-candidate sweep structure sound? | compare Agency Surface, Oxidized Toolchain, and Movement 1 Substrate as training lanes |
| Should Agency Surface remain first? | evaluate whether skill/MCP/doc rot should precede toolchain hardening |
| What should a returned research result look like to be maximally useful? | propose an output schema |

### 4.2 Required Gap Analysis

Return a lossless gap table:

| Gap ID | Plan location | Claim or omission | Why it matters | Evidence needed | Suggested repair |
|---|---|---|---|---|---|

Use severity levels:

| Severity | Meaning |
|---|---|
| Critical | can invert the plan or cause wrong execution |
| High | likely to create false positives |
| Medium | weakens repeatability |
| Low | clarity or formatting issue |

### 4.3 Required Invariant Extraction

Extract the plan's stable invariants separately from local inventory facts.

Use this table:

| Stable invariant | Why stable | Local example | How to generalize |
|---|---|---|---|

Example:

```text
Declared != reachable != healthy != authoritative
```

is a stable invariant.

```text
uv is version 0.11.25
```

is local inventory, not an invariant.

### 4.4 Required False-Positive Audit

Find likely remaining false positives.

Use this table:

| False-positive risk | Where it appears | How it could mislead an agent | Countermeasure |
|---|---|---|---|

Pay special attention to:

- skills used to audit skills;
- MCP config names versus runtime availability;
- tool doctors and stale scripts;
- dot-folder versus non-dot folder naming;
- local Windows PATH versus nested/private toolchains;
- rich style masking weak execution criteria;
- "do not do X" overload becoming cognitive noise.

### 4.5 Required Output Schema Design

The next version of this plan needs a return format that is not harder to use than the plan itself.

Design a result schema with:

| Section | Purpose | Required fields |
|---|---|---|

The schema should support triangulation between two research agents.

## 5. Model Pair Instructions

If this brief is sent to two research agents, split their emphasis.

### 5.1 Pro / Long-Context Lane

Role:

```text
Structural epistemic auditor.
```

Primary focus:

- hidden assumptions;
- invariants versus local facts;
- plan structure;
- false-positive taxonomy;
- lossless gap analysis;
- downstream usefulness.

Return:

- prioritized findings;
- invariant table;
- gap table;
- proposed revised framing.

### 5.2 Flash / Fast-Adversarial Lane

Role:

```text
Practical adversarial executor.
```

Primary focus:

- where an agent would misunderstand the plan;
- which instructions are too ornate or too implicit;
- what a tired coding agent would do wrong;
- which commands or file references are dangerous, stale, or overfit;
- what minimum schema would make the plan actionable.

Return:

- top failure modes;
- "agent would likely do X wrong" table;
- simplification suggestions that do not reduce the plan's intelligence;
- execution-readiness score.

## 6. What Not To Do

Do not:

- summarize the plan as if summary equals analysis;
- convert it into a generic corporate checklist;
- remove the creative register unless it blocks execution;
- assume local inventory facts are current forever;
- assume the plan's own confidence is justified;
- propose broad rewrites without preserving the intent;
- tell the user to install a linter, a second extension, or a new dependency as the first answer;
- treat a skill, script, MCP config, or README as truth without external proof;
- spend the response explaining basic project management.

## 7. What To Return

Return the following sections, in this order:

### 7.1 Findings First

| Rank | Severity | Finding | Why it matters | Fix |
|---:|---|---|---|---|

### 7.2 Invariants vs Local Facts

| Item | Type | Keep in plan? | Notes |
|---|---|---:|---|

Type must be one of:

- stable invariant;
- current local fact;
- hypothesis;
- stale-risk artifact;
- style/voice element.

### 7.3 Lossless Gap Analysis

Use the required gap table from section 4.2.

### 7.4 False-Positive Taxonomy

Return a taxonomy that can be reused in future plans.

### 7.5 Best Next Version

Provide a short outline for Plan v2.

Do not rewrite the whole plan unless explicitly asked. Provide the outline and the highest-leverage edits.

### 7.6 Triangulation Notes

If you are one of two models, state what the other model should verify.

## 8. Evaluation Rubric

Score the plan from 1-10 in each dimension:

| Dimension | Score | Why | Repair |
|---|---:|---|---|
| Cold-start clarity |  |  |  |
| False-positive resistance |  |  |  |
| Inventory discipline |  |  |  |
| Actionability |  |  |  |
| Anti-hallucination strength |  |  |  |
| Context preservation |  |  |  |
| Style-to-signal balance |  |  |  |
| Research-boomerang readiness |  |  |  |

## 9. Final Constraint

The return should make the originating session smarter without forcing it to become smaller.

The goal is not to reduce the plan. The goal is to frame it so a cold research agent can bring back hidden structure, better distinctions, and higher-confidence next moves.

