# Skill Tensor — Parity State & System Explanation

> Generated: 2026-03-20

---

## Current Skill Parity State

| Skill | Claude (33) | Codex (28) | Gemini (28) |
|-------|:-----------:|:----------:|:-----------:|
| **Core 27** (shared by all three) | Yes | Yes | Yes |
| git-snapshot | Yes | - | - |
| handoff-loop | Yes | - | - |
| overnight-archaeology | Yes | - | - |
| sfa | Yes | - | - |
| theme-system | Yes | - | - |
| link-path-guard | Yes | Yes | - |
| triad-velocity-lane | - | - | Yes |

**Claude has 33 skills, Codex has 28, Gemini has 28.** They share a common core of 27. Claude is the superset — 5 skills exist only in Claude, 1 only in Gemini, and `link-path-guard` is in Claude+Codex but not Gemini.

---

## How to Explain the System

The system is a **skill tensor** — a combinatorial matrix of *who runs what, on whom, using which skill*.

### The Three Dimensions

Every execution has three variables:

1. **Operator** (who runs it): Claude, Codex, or Gemini
2. **Skill** (what runs): any of the N shared skills
3. **Target** (run on whom): Claude's lane, Codex's lane, or Gemini's lane

### The Combinatorics

With **1 agent, N skills**: `N` possible actions (agent runs each skill on itself).

With **2 agents, N skills**: `N × 4` — each skill can be run as:

- A runs skill on A
- A runs skill on B
- B runs skill on A
- B runs skill on B

With **3 agents, N skills**: `N × 9` — each skill has a 3×3 operator×target matrix:

```
           Target →  Claude    Codex     Gemini
Operator ↓
Claude              C→skill→C  C→skill→X  C→skill→G
Codex               X→skill→C  X→skill→X  X→skill→G
Gemini              G→skill→C  G→skill→X  G→skill→G
```

So for **N skills across 3 agents**: the tensor pool = **N × 3 × 3 = 9N** possible cells.

With the target parity of **27 shared skills**: that's **243 cells** in the tensor pool. The roulette picks one cell at random from this pool via true RNG.

### Why Parity Matters

If skills aren't equal across all three, the tensor has holes — some cells are invalid (an agent can't run a skill it doesn't have, or target a lane that doesn't have the skill). Parity means every cell in the 9N pool is a legal execution. Without parity, you need a **legality gate** to filter out invalid cells before the RNG picks.

### What `skill_tensor_cycle.py` Does (Single-File Constraint)

The script must be self-contained because it's the **neutral arbiter** — it can't live inside any one agent's skill tree without bias. It:

1. **Inventories** all three skill roots to build the pool
2. **Classifies** each skill (candidate vs redirect/stub)
3. **Generates the tensor** — all legal operator×skill×target combinations
4. **Picks via RNG** from the pool
5. **Dispatches** through adapter shims (since each skill has a different execution mode)

All of this stays in one `.py` because splitting it across files would mean the tensor logic depends on imports from agent-specific paths — breaking neutrality.

---

## Step 1: Equalize to Parity

To achieve a clean `N × 9` tensor with no legality holes:

- **Codex needs**: `git-snapshot`, `handoff-loop`, `overnight-archaeology`, `sfa`, `theme-system`
- **Gemini needs**: `link-path-guard`, `git-snapshot`, `handoff-loop`, `overnight-archaeology`, `sfa`, `theme-system`
- **Decide on**: `triad-velocity-lane` (Gemini-only) — promote to all three or remove

Once parity is achieved, the tensor pool is a clean `N × 9` grid and every RNG pick is guaranteed legal.
